import os
import uuid
import shutil
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Literal, cast
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.parsers import extract_text_from_pdf
from app.services.chunker import ChunkerService
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStoreService
from app.models.db import AsyncSessionLocal, Document

router = APIRouter()

chunker = ChunkerService()
embedder = EmbedderService()
vector_store = VectorStoreService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    strategy: Literal["recursive", "semantic"] = Form("recursive"),
):
    """
    Upload a PDF or TXT file
    """
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")


    temp_path = f"/tmp/{uuid.uuid4()}_{filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # extract text
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(temp_path)
        else:
            with open(temp_path, "r", encoding="utf-8") as f:
                text = f.read()

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

        # chunkinf the text
        if strategy == "semantic":
            chunks = chunker.semantic_chunking(text)
        else:
            chunks = chunker.recursive_chunking(text)

        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks were created from the file text.")

        if len(chunks) > 300:
            raise HTTPException(
                status_code=400,
                detail="Document is too large after chunking (max 300 chunks). Upload a smaller file.",
            )

        # Embed and store in Qdrant
        try:
            embeddings = await asyncio.wait_for(embedder.get_embeddings(chunks), timeout=90)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Embedding timed out. Please try a smaller file.")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Embedding failed: {e}")

        try:
            await asyncio.wait_for(
                vector_store.upsert_vectors(chunks, embeddings, {"filename": filename}),
                timeout=90,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Vector store upsert timed out. Please retry.")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Vector store upsert failed: {e}")

        # Save data to databseee
        async with cast(AsyncSession, AsyncSessionLocal()) as session:
            doc = Document(
                filename=filename,
                chunk_count=len(chunks),
                chunking_strategy=strategy,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)

        return {
            "message": "Ingestion successful",
            "chunks": len(chunks),
            "strategy": strategy,
            "document_id": doc.id,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/documents")
async def get_ingested_documents(limit: int = 50, offset: int = 0):
    """Return ingested document metadata stored in SQLite."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    async with cast(AsyncSession, AsyncSessionLocal()) as session:
        query = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(query)
        docs = result.scalars().all()

    return {
        "count": len(docs),
        "limit": limit,
        "offset": offset,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "chunk_count": doc.chunk_count,
                "chunking_strategy": doc.chunking_strategy,
                "created_at": (
                    created_at.isoformat() if (created_at := getattr(doc, "created_at", None)) else None
                ),
            }
            for doc in docs
        ],
    }

import os
import uuid
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

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
UPLOAD_READ_TIMEOUT_SECONDS = 30
TEXT_EXTRACTION_TIMEOUT_SECONDS = 60
CHUNKING_TIMEOUT_SECONDS = 30


def _write_temp_file(path: str, content: bytes) -> None:
    with open(path, "wb") as f:
        f.write(content)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    strategy: Literal["recursive", "semantic"] = Form("recursive"),
):
    """
    Upload a PDF or TXT file
    """
    filename = os.path.basename((file.filename or "").strip())
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = os.path.splitext(filename)[1].lower()
    if extension not in {".pdf", ".txt"}:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")


    temp_path = f"/tmp/{uuid.uuid4()}_{filename}"

    try:
        try:
            file_bytes = await asyncio.wait_for(file.read(), timeout=UPLOAD_READ_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Upload read timed out. Please retry.")

        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        if len(file_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File is too large (max 10 MB). Upload a smaller PDF/TXT file.",
            )

        await asyncio.to_thread(_write_temp_file, temp_path, file_bytes)

        # extract text
        if extension == ".pdf":
            try:
                text = await asyncio.wait_for(
                    asyncio.to_thread(extract_text_from_pdf, temp_path),
                    timeout=TEXT_EXTRACTION_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="PDF text extraction timed out.")
        else:
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="TXT file must be valid UTF-8.")

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

        # chunkinf the text
        try:
            if strategy == "semantic":
                chunks = await asyncio.wait_for(
                    asyncio.to_thread(chunker.semantic_chunking, text),
                    timeout=CHUNKING_TIMEOUT_SECONDS,
                )
            else:
                chunks = await asyncio.wait_for(
                    asyncio.to_thread(chunker.recursive_chunking, text),
                    timeout=CHUNKING_TIMEOUT_SECONDS,
                )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Text chunking timed out. Please upload a smaller file.")

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
        await file.close()
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

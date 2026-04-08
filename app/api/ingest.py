import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Literal
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
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")


    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # extract text
        if file.filename.endswith(".pdf"):
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

        # Embed and store in Qdrant
        embeddings = await embedder.get_embeddings(chunks)
        await vector_store.upsert_vectors(chunks, embeddings, {"filename": file.filename})

        # Save data to databseee
        async with AsyncSessionLocal() as session:
            doc = Document(
                filename=file.filename,
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

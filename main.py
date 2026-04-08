from fastapi import FastAPI
from app.api import ingest, chat
from app.models.db import init_db
import contextlib


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Create SQLite tables on startup if they don't exist
    await init_db()
    yield


app = FastAPI(
    title="Palm RAG API",
    description="Document ingestion and conversational RAG with interview booking",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
async def root():
    return {
        "name": "Palm RAG API",
        "endpoints": [
            "POST /ingest/upload - Upload PDF/TXT documents",
            "POST /chat - RAG Q&A or interview booking",
            "GET  /chat/history/{session_id} - Get chat history",
            "GET  /chat/bookings - List all bookings"
        ]
    }

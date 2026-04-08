from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal, Dict, Any

class IngestResponse(BaseModel):
    message: str
    chunks: int
    strategy: str
    document_id: Optional[int] = None


# chat ko resp

class Source(BaseModel):
    text: str
    metadata: Dict[str, Any]
    score: float


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Unique session ID for chat memory")
    mode: Optional[Literal["rag", "booking"]] = Field(
        default=None,
        description="Optional: 'rag' for document Q&A, 'booking' for interview booking. Auto-detected if not provided."
    )


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    mode: str
    sources: Optional[List[Source]] = None   # filled in rag mode
    booking: Optional[Dict[str, Any]] = None  # filled in booking mode


class BookingData(BaseModel):
    id: int
    name: str
    email: EmailStr
    date: str   # YYYY-MM-DD
    time: str   # HH:MM (24hr)
    created_at: Optional[str] = None

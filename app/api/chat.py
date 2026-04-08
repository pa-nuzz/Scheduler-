import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.models.schemas import ChatRequest, ChatResponse
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStoreService
from app.services.memory import MemoryService
from app.services.llm import LLMService
from app.services.rag_pipeline import RAGPipeline
from app.services.booking import BookingService

router = APIRouter()

embedder = EmbedderService()
vector_store = VectorStoreService()
memory = MemoryService()
llm = LLMService()
rag = RAGPipeline(embedder, vector_store, memory, llm)


def _validate_session_id(session_id: str) -> str:
    """Normalize and validate session IDs used for Redis chat memory keys."""
    normalized = session_id.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="session_id cannot be empty")
    if len(normalized) > 128:
        raise HTTPException(status_code=400, detail="session_id is too long (max 128 chars)")
    return normalized


async def detect_intent(message: str) -> str:
    """
    Auto-detect if the user wants to book an interview or ask a question.
    
    Returns: "booking" or "rag"
    """
    prompt = f"""Classify the user's intent.

Message: "{message}"

Is this about booking/scheduling an interview? Reply with ONLY one word: "booking" or "rag".

Examples:
- "Book me for tomorrow" → booking
- "I want to schedule an interview" → booking
- "What is machine learning?" → rag
- "Tell me about the document" → rag

Answer:"""
    
    response = await llm.generate_answer(prompt)
    intent = response.strip().lower()
    
    # Default to rag if unclear
    if intent not in ("booking", "rag"):
        return "rag"
    return intent


async def extract_booking_with_llm(message: str) -> Dict[str, Any]:
    """
    Use the LLM to extract booking details from a natural language message.

    We prompt the LLM to return JSON with name, email, date, and time.
    This handles any phrasing the user might use, not just fixed patterns.
    """
    prompt = f"""Extract interview booking details from this message.
Return ONLY a valid JSON object with these exact keys: name, email, date, time.
- date format: YYYY-MM-DD
- time format: HH:MM (24-hour)
- Use null for any field that is not mentioned.

Message: {message}

JSON:"""

    response = await llm.generate_answer(prompt)

    # Strip markdown code if the LLM wrapped the JSON
    response = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        #  yedi input ki presing fails treat all fields as missing
        data = {"name": None, "email": None, "date": None, "time": None}

    # collect wich required fields are still missing
    data["missing_fields"] = [
        field for field in ["name", "email", "date", "time"]
        if not data.get(field)
    ]

    return data


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    chat endpoint — supports RAG Q&A and interview booking.
                      
    """
    
    valid_session_id = _validate_session_id(request.session_id)

    # detect mode if mode is not provided
    mode = request.mode
    if mode is None:
        mode = await detect_intent(request.message)

    # ── RAG MODE ──────────────────────────────────────────────────────────────
    if mode == "rag":
        try:
            result = await rag.run(request.message, valid_session_id)
            return ChatResponse(
                answer=result["answer"],
                session_id=valid_session_id,
                mode="rag",
                sources=result.get("sources", []),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"RAG processing failed: {e}")

    elif mode == "booking":
        try:
            # LLM extracts booking info from the user's message
            parsed = await extract_booking_with_llm(request.message)
            name = parsed.get("name")
            email = parsed.get("email")
            date = parsed.get("date")
            time = parsed.get("time")
            missing = parsed.get("missing_fields", [])

            # for missing fields asking the user
            if missing:
                msg = (
                    f"To book your interview I still need: {', '.join(missing)}.\n"
                    "Please provide: name, email, date (YYYY-MM-DD), and time (HH:MM)."
                )
                await memory.save(valid_session_id, request.message, msg)
                return ChatResponse(
                    answer=msg,
                    session_id=valid_session_id,
                    mode="booking",
                    booking=None,
                )

            result = await BookingService.create_booking(name, email, date, time)

            if result["success"]:
                booking = result["booking"]
                confirmation = (
                    f"Your interview has been booked!\n\n"
                    f"Name:  {booking['name']}\n"
                    f"Email: {booking['email']}\n"
                    f"Date:  {booking['date']}\n"
                    f"Time:  {booking['time']}\n"
                    f"Booking ID: {booking['id']}"
                )
                await memory.save(valid_session_id, request.message, confirmation)
                return ChatResponse(
                    answer=confirmation,
                    session_id=valid_session_id,
                    mode="booking",
                    booking=booking,
                )
            else:
                error_msg = f"Booking failed: {result.get('error', 'Unknown error')}"
                await memory.save(valid_session_id, request.message, error_msg)
                return ChatResponse(
                    answer=error_msg,
                    session_id=valid_session_id,
                    mode="booking",
                    booking=None,
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Booking processing failed: {e}")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mode '{mode}'. Use 'rag' or 'booking'.",
        )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Return the last 20 messages for this session from Redis."""
    valid_session_id = _validate_session_id(session_id)
    history = await memory.get_history(valid_session_id, limit=20)
    return {"session_id": valid_session_id, "history": history}


@router.delete("/history/{session_id}")
async def delete_chat_history(session_id: str):
    """Delete all stored Redis chat history for a session."""
    valid_session_id = _validate_session_id(session_id)
    await memory.clear_history(valid_session_id)
    return {"message": "Chat history deleted", "session_id": valid_session_id}


@router.get("/bookings")
async def list_bookings(email: str = None):
    """List all bookings from SQLite. Pass ?email= to filter by email."""
    bookings = await BookingService.get_bookings(email)
    return {"bookings": bookings}

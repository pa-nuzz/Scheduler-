# Scheduler RAG API
This ia a backend api for uploading documents and conversational rag and interview booking. 

## Project Summary (Detailed)
This is a FastAPI backend for document-based AI chat plus interview scheduling. Users upload PDF or TXT files, the system extracts text, applies selectable chunking strategies, generates embeddings, stores vectors in Qdrant, and stores metadata/bookings in SQLite. The chat API supports multi-turn conversations using Redis memory and runs a custom RAG pipeline (not RetrievalQAChain). It also detects booking intent, extracts name/email/date/time via LLM, validates details, and stores confirmed bookings.

## About the project

1. Document upload and upload pdf or txt files, extract text and split into chunks and generate embeddings and store in qdrant cloud for similarity search and save metadata in sqlite.(db can be upgraded)

2. Chat and interview booking : Two modes:
   - **RAG Mode**: Ask questions about uploaded document.The system retrieves relevant chunks info and generate answers.
   - **Booking Mode**: Book interviews via llm. It  extracts name, email, date, and time.


## Architecture
![alt text](palmarchi.png)

## Demo video
<video controls src="Untitled.mp4" title="<video controls src="Untitled.mov" title="Title"></video>"></video>

### Tech Stack
- Fastapi - (api framework)
- sqlite - (metadata and booking)
- Qdrant - (vector store)
- Redis cloud - (chat session memory)
- llm- gemini(primary), if fallback->(Groq)

## API Endpoints
- POST /ingest/upload (for upload)
- GET /ingest/documents (list ingested document metadata)
- POST /chat (chat and booking)
- GET /chat/history/{session_id} (for get session chat)
- DELETE /chat/history/{session_id} (delete session chat history)
- GET /chat/bookings (for get all booking )

### API Count 
- I built 2 core REST APIs:
   1. Document Ingestion API
   2. Conversational RAG API (with interview booking flow)
- Total implemented endpoints currently: 6 functional endpoints (plus root endpoint / for API info).


## Setup

Install dependencies:
pip install -r requirements.txt

If you already had the old SDK installed, refresh the environment:
pip uninstall -y google-generativeai
pip install -U -r requirements.txt

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
QDRANT_URL=...
QDRANT_API_KEY=...
GOOGLE_API_KEY=...
GROQ_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=gemini-embedding-001
REDIS_URL=redis://user:pass@host:port
```

Run the server:
uvicorn main:app --reload

Test API:
curl http://localhost:8000/

## How It Works

### Document ingestion 
user uploads the pdf or txt file
and text is extracted and chunked using chunker service and gemini does the embedding, 
vectors are stored in qdrant cloud and file metadata is saved
to sqlite. 

### RAG
user askes question,embed it with gemini and searches qdrant for similar chunks.And llm generates the answer with sources and the convo is saved in redis 

### Booking 
user sends booking request, if no field is missing,(if missing field,it asks user to input correctly)
it validates and saves to db and return with booking id. 

## Chunking 
- recursive (Fixed-size character chunks (800 chars) with 100-char overlap. It prevents context loss at chunk boundaries.)

- semantic (Groups sentences together (4 per chunk). Preserves natural language boundaries.)

## Error Handling

- Invalid file types → 400 Bad Request
- Missing fields in booking → Ask user for them
- Service unavailable → 500 with clear message
- Redis down → Chat continues without history


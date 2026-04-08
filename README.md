# Palm RAG API
This ia a backend api for uploading documents and conversational rag and interview booking. 

## About the project

1. Document upload and : Upload pdf or txt files, extract text and split into chunks and generate embeddings and store in qdrant cloud for similarity search and save metadata in sqlite.(db can be upgraded)

2. Chat and interview booking : Two modes:
   - **RAG Mode**: Ask questions about uploaded document.The system retrieves relevant chunks info and generate answers.
   - **Booking Mode**: Book interviews via llm. It  extracts name, email, date, and time.

## Architecture
![alt text](palmarchi.png)

### Tech Stack
Fastapi - api framework
sqlite - metadata and booking
Qdrant - vector store
Redis cloud - chat session memory
llm- gemini(primary), if fallback->(Groq)

## API Endpoints
POST /ingest/upload (for upload)
POST /chat (chat and booking)
GET /chat/history/{session_id} (for get session chat)
GET /chat/bookings (for get all booking )


## Setup

Install dependencies:
pip install -r requirements.txt

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
QDRANT_URL=...
QDRANT_API_KEY=...
GOOGLE_API_KEY=...
GROQ_API_KEY=...
REDIS_URL=redis://user:pass@host:port
```

Run the server:
uvicorn main:app --reload

Test API:
curl http://localhost:8000/

## How It Works

### Document ingestion 
user uploads the pdf or txt file
and text is extracted and chunked using gemini and 
vectors are stored in qdrant cloud and data is saved
to sqlite. 

### RAG
user askes question,embed it with geminu and searches qdrant for similar chunks.And llm generates the answer with sources and the convo is saved in redis 

### Booking 
user sends booking request, if no field is missing,
it validates and saves to db and return with booking id. 

## Chunking 
recursive and semantic

## Error Handling

- Invalid file types → 400 Bad Request
- Missing fields in booking → Ask user for them
- Service unavailable → 500 with clear message
- Redis down → Chat continues without history


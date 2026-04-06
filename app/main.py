from fastapi import FastAPI
from api.endpoints import ingest, chat

app = FastAPI()

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

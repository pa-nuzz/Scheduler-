import google.generativeai as genai
from typing import List
from app.core.config import settings

EMBEDDING_MODEL = "models/gemini-embedding-001"


class EmbedderService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def get_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        
        embeddings = []
        for chunk in text_chunks:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=chunk,
                task_type="retrieval_document",
            )
            embeddings.append(result["embedding"])
        return embeddings

    async def get_query_embedding(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]

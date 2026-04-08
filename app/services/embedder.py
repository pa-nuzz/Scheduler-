from google import genai
from typing import List
import asyncio
from app.core.config import settings

class EmbedderService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL

    @staticmethod
    def _extract_embedding(result: object) -> List[float]:
        """Extract embedding values from the google.genai response object."""
        embeddings = getattr(result, "embeddings", None)
        if embeddings and len(embeddings) > 0:
            first = embeddings[0]
            values = getattr(first, "values", None)
            if values:
                return list(values)

        single = getattr(result, "embedding", None)
        if single:
            values = getattr(single, "values", None)
            if values:
                return list(values)

        raise RuntimeError("Embedding response did not contain vector values")

    async def get_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        embeddings = []
        for chunk in text_chunks:
            result = await asyncio.to_thread(
                self.client.models.embed_content,
                model=self.embedding_model,
                contents=chunk,
            )
            embeddings.append(self._extract_embedding(result))
        return embeddings

    async def get_query_embedding(self, text: str) -> List[float]:
        result = await asyncio.to_thread(
            self.client.models.embed_content,
            model=self.embedding_model,
            contents=text,
        )
        return self._extract_embedding(result)

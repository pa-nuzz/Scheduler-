import uuid
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

EMBEDDING_DIMENSION = 3072  # Gemini embedding-001 output size
UPSERT_BATCH_SIZE = 16


class VectorStoreService:
    """Handles all interactions with Qdrant Cloud (store and search vectors)."""

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=60,
        )
        self.collection_name = settings.COLLECTION_NAME

    def _ensure_collection(self):
        """Create the Qdrant collection if it doesn't exist yet"""
        try:
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            raise RuntimeError(f"Failed to setup Qdrant collection: {e}")

    async def upsert_vectors(self, chunks: list, embeddings: list, metadata: dict):
        """
        Store document chunks and their embeddings in qdrant
        """
        await asyncio.to_thread(self._ensure_collection)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": chunk, "metadata": metadata},
            )
            for chunk, vector in zip(chunks, embeddings)
        ]

        # Upload in small batches to avoid timeouts
        for i in range(0, len(points), UPSERT_BATCH_SIZE):
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points[i:i + UPSERT_BATCH_SIZE],
            )

    async def search(self, query_vector: list, top_k: int = 5) -> list:
        """
        Find the top-K most similar chunks to the query vector.
        retrival step in rag for closestmeaning 
        """
        await asyncio.to_thread(self._ensure_collection)

        response = await asyncio.to_thread(
            self.client.query_points,
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "text": point.payload.get("text", "") if point.payload else "",
                "metadata": point.payload.get("metadata", {}) if point.payload else {},
                "score": point.score,
            }
            for point in response.points
        ]

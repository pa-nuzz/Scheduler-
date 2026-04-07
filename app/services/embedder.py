import google.generativeai as genai
from app.core.config import settings

class EmbedderService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def get_embeddings(self, text_chunks: List[str]):
        
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_chunks,
            task_type="retrieval_document")
        
        return result['embedding']
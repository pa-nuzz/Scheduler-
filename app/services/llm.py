import asyncio
from google import genai
from groq import Groq
from app.core.config import settings

GEMINI_TIMEOUT_SECONDS = 45
GROQ_TIMEOUT_SECONDS = 45


class LLMService:
   

    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.gemini_model_name = settings.GEMINI_MODEL
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

    def _gemini_generate(self, prompt: str) -> str:
        response = self.gemini_client.models.generate_content(
            model=self.gemini_model_name,
            contents=prompt,
        )
        if getattr(response, "text", None):
            return response.text
        return str(response)

    def _groq_generate(self, prompt: str) -> str:
        completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return completion.choices[0].message.content

    async def generate_answer(self, prompt: str) -> str:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._gemini_generate, prompt),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
        except Exception as gemini_error:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self._groq_generate, prompt),
                    timeout=GROQ_TIMEOUT_SECONDS,
                )
            except Exception as groq_error:
                raise RuntimeError(
                    f"All LLM providers failed (Gemini: {gemini_error}; Groq: {groq_error})"
                )

from google import genai
from groq import Groq
from app.core.config import settings


class LLMService:
   

    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.gemini_model_name = settings.GEMINI_MODEL
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

    async def generate_answer(self, prompt: str) -> str:
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_name,
                contents=prompt,
            )
            if getattr(response, "text", None):
                return response.text
            return str(response)
        except Exception as e:
            print(f"Gemini failed ({e}), switching to Groq...")
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            return completion.choices[0].message.content

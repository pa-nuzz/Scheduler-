import google.generativeai as genai
from groq import Groq
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate_answer(self, prompt: str):
        try:
            # Primary: Gemini
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini failed, switching to Groq: {e}")
            # Fallback: Groq (Llama 3.1)
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            return chat_completion.choices[0].message.content





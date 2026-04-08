from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    QDRANT_URL: str
    QDRANT_API_KEY: str
    COLLECTION_NAME: str = "Scheduler_collection"

    REDIS_URL: str

    DATABASE_URL: str = "sqlite+aiosqlite:///./palm.db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()  # type: ignore[call-arg]

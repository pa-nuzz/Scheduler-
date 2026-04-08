from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str

    QDRANT_URL: str
    QDRANT_API_KEY: str
    COLLECTION_NAME: str = "palm_collection"

    REDIS_URL: str

    DATABASE_URL: str = "sqlite+aiosqlite:///./palm.db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

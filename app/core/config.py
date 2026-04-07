#this file handles the api keys and settings. using pydantic-settings bc it auto reads the env file
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #API KEY
    Gemini_API_KEY: str
    Groq_API_KEY: str

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str
    Collection_NAME: str = "palm_collection"

    #Redis
    REDIS_HOST: str = "redis://localhost:6379"

    #Database
    DB_HOST: str = "sqlite+aiosqlite:///./palm.db"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()


import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

Base = declarative_base()


class Document(Base):
    """Tracks uploaded documents — actual content lives in Qdrant as vectors."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    chunking_strategy = Column(String, nullable=False)  # "recursive" or "semantic"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Booking(Base):
    """Stores interview bookings created through the chat API."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    date = Column(String, nullable=False)   # YYYY-MM-DD
    time = Column(String, nullable=False)   # HH:MM
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


engine = create_async_engine(settings.DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

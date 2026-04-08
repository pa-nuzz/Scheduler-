import json
import redis.asyncio as redis
from typing import List, Dict, Any
from app.core.config import settings


class MemoryService:
   
    def __init__(self):
        self.redis_client = None
        self._connected = False

    async def _ensure_connection(self):
        if self._connected:
            return
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            self._connected = True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self._connected = False

    async def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the last N message pairs for this session."""
        await self._ensure_connection()
        if not self._connected:
            return []
        try:
            raw = await self.redis_client.lrange(f"chat:{session_id}", -limit, -1)
            return [json.loads(item) for item in raw if item]
        except Exception as e:
            print(f"Failed to get history: {e}")
            return []

    async def save(self, session_id: str, user_message: str, assistant_response: str):
        """Append a message pair and refresh the 24hr expiry."""
        await self._ensure_connection()
        if not self._connected:
            return
        try:
            key = f"chat:{session_id}"
            entry = {"user": user_message, "assistant": assistant_response}
            await self.redis_client.rpush(key, json.dumps(entry))
            await self.redis_client.expire(key, 86400)  # 24 hours
        except Exception as e:
            print(f"Failed to save to Redis: {e}")

    async def clear_history(self, session_id: str):
        """Delete all messages for this session."""
        await self._ensure_connection()
        if not self._connected:
            return
        try:
            await self.redis_client.delete(f"chat:{session_id}")
        except Exception as e:
            print(f"Failed to clear history: {e}")

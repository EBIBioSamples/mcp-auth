import hashlib
import json

from redis.asyncio import Redis
from app.core.config import Settings

class RedisConfig:
    def __init__(self):
         self.redis = Redis.from_url(
            Settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )

    @staticmethod
    def _cache_key(username) -> str:
        raw = json.dumps(
            username,
            sort_keys=True,
            default=str,
        )

        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return f"tool-cache:{username}:{digest}"

    async def cache_token(self, username, response:str)-> None:
        cache_key = self._cache_key(username)

        await self.redis.set(
                cache_key,
                response,
            300,
        )
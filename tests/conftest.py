from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


try:
    import redis.asyncio
    from redis.exceptions import RedisError

except ModuleNotFoundError:
    redis_module = types.ModuleType("redis")
    redis_asyncio_module = types.ModuleType("redis.asyncio")
    redis_exceptions_module = types.ModuleType("redis.exceptions")

    class RedisError(Exception):
        pass

    class Redis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            instance = cls()
            instance.setex = AsyncMock()
            instance.get = AsyncMock()
            instance.delete = AsyncMock()
            return instance

    redis_asyncio_module.Redis = Redis
    redis_exceptions_module.RedisError = RedisError

    redis_module.asyncio = redis_asyncio_module
    redis_module.exceptions = redis_exceptions_module

    sys.modules["redis"] = redis_module
    sys.modules["redis.asyncio"] = redis_asyncio_module
    sys.modules["redis.exceptions"] = redis_exceptions_module
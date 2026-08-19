from __future__ import annotations
from pathlib import Path
from unittest.mock import AsyncMock

import sys
import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import redis.asyncio  # noqa: F401
except ModuleNotFoundError:
    redis_module = types.ModuleType("redis")
    redis_asyncio_module = types.ModuleType("redis.asyncio")

    class Redis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            instance = cls()
            instance.setex = AsyncMock()
            return instance

    redis_asyncio_module.Redis = Redis
    redis_module.asyncio = redis_asyncio_module
    sys.modules["redis"] = redis_module
    sys.modules["redis.asyncio"] = redis_asyncio_module
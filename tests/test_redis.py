import hashlib
import json
from unittest.mock import AsyncMock

import pytest

from app.core.redis import RedisConfig

def test_cache_key_is_deterministic():
    username = "test-user"
    raw = json.dumps(username, sort_keys=True, default=str)
    expected_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    key1 = RedisConfig._cache_key(username)
    key2 = RedisConfig._cache_key(username)

    assert key1 == key2
    assert key1 == f"tool-cache:{username}:{expected_digest}"

@pytest.mark.asyncio
async def test_cache_token_stores_token_for_300_seconds():
    redis_config = RedisConfig()
    redis_config.redis = AsyncMock()

    await redis_config.cache_token(
        username="test-user",
        response="jwt-token-123",
    )

    expected_key = RedisConfig._cache_key("test-user")
    redis_config.redis.set.assert_awaited_once_with(
        expected_key,
        "jwt-token-123",
        300,
    )
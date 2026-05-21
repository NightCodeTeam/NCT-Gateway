import time
import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import redis.asyncio as redis_a
from httpx import AsyncClient, ASGITransport

from src.gateway.limiter import TokenBucket
from src.gateway.base import GatewayProcessor, App
from src.__main__ import app

from core.redis_client import RedisClient


@pytest.fixture
def mock_redis():
    """Создает мок для Redis"""
    mock = AsyncMock(spec=redis_a.Redis)
    mock_data = {}
    mock_expires = {}

    async def mock_get(key):
        return mock_data.get(key)

    async def mock_set(key: str, value: str, ex: int):
        mock_data[key] = value
        mock_expires[key] = time.time() + ex
        return None

    async def mock_delete(key: str):
        mock_data.pop(key, None)
        mock_expires.pop(key, None)
        return None

    async def mock_scan_iter(key: str):
        for k in list(mock_data.keys()):
            if key[:-1] in k:
                yield k

    async def mock_unlink(key: str):
        return mock_delete(key)

    mock.get.side_effect = mock_get
    mock.set.side_effect = mock_set
    mock.delete.side_effect = mock_delete
    mock.unlink.side_effect = mock_unlink
    mock.scan_iter.side_effect = mock_scan_iter
    return mock


@pytest.fixture
def mock_redis_pool():
    """Мок пула соединений"""
    return MagicMock(spec=redis_a.ConnectionPool)


@pytest.fixture
async def redis_client(mock_redis, mock_redis_pool):
    """Создает экземпляр RedisClient с замоканным Redis"""
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        client = RedisClient(mock_redis_pool, "test_prefix", expire=3600)
        # Заменяем приватный клиент на наш мок
        client._RedisClient__client = mock_redis
        return client


@pytest.fixture
def token_bucket():
    """Fixture for a standard token bucket initialization."""
    return TokenBucket(rate=10, burst=10)


@pytest.fixture
def processor(redis_client):
    """Создает экземпляр GatewayProcessor с моком RedisClient."""
    return GatewayProcessor(redis_client, apps=(
        App(
            name='app_1',
            redirect_url='http://localhost:8080',
            allowed_methods=('GET', 'POST'),
        ),
        App(name='app_2', redirect_url='http://localhost:8081'),
    ))


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

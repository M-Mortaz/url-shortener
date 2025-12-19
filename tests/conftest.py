"""Pytest configuration and fixtures for async tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.id_generator import SnowflakeIDGenerator
from app.core.id_service import set_id_generator


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database engine and session."""
    # Use in-memory SQLite for testing
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    yield async_session
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    
    # Set up default return values
    # RedisCache uses redis.get() and redis.setex()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.delete = AsyncMock(return_value=1)
    
    return redis_mock


@pytest.fixture(scope="function")
async def mock_analytics():
    """Mock analytics publisher."""
    analytics_mock = AsyncMock()
    analytics_mock.publish_click_event = AsyncMock(return_value=None)
    return analytics_mock


@pytest.fixture(scope="function")
async def mock_id_generator():
    """Mock ID generator."""
    generator = MagicMock(spec=SnowflakeIDGenerator)
    generator.generate.return_value = 1234567890123456789
    generator.generate_short_code.return_value = "test123"
    return generator


@pytest.fixture(scope="function")
async def client(test_db, mock_redis, mock_analytics, mock_id_generator):
    """Create a test client with mocked dependencies."""
    # Set up ID generator
    set_id_generator(mock_id_generator)
    
    # Override dependencies in app
    async def override_get_session():
        async with test_db() as session:
            yield session
    
    async def override_get_redis():
        return mock_redis
    
    async def override_get_analytics():
        return mock_analytics
    
    from app.db.session import get_session
    from app.core.redis_client import get_redis_client
    from app.core.analytics import get_analytics_publisher
    
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis_client] = override_get_redis
    app.dependency_overrides[get_analytics_publisher] = override_get_analytics
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


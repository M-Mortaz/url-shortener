"""Tests for GET /{short_code} redirect endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from unittest.mock import AsyncMock

from app.db.models import ShortURL


@pytest.mark.asyncio
async def test_redirect_with_cache_hit(client: AsyncClient, mock_redis):
    """Test redirect when URL is found in Redis cache."""
    # Mock Redis to return cached URL (RedisCache adds "short_url:" prefix)
    mock_redis.get = AsyncMock(return_value="https://example.com/cached")
    
    response = await client.get("/test123", follow_redirects=False)
    
    assert response.status_code == 301
    assert response.headers["location"] == "https://example.com/cached"


@pytest.mark.asyncio
async def test_redirect_with_cache_miss(client: AsyncClient, test_db, mock_redis):
    """Test redirect when URL is found in database (cache miss)."""
    # Mock Redis to return None (cache miss)
    mock_redis.get = AsyncMock(return_value=None)
    
    # Create a short URL in the test database
    async with test_db() as session:
        short_url = ShortURL(
            snowflake_id=1234567890123456789,
            original_url="https://example.com/database",
            short_code="db123"
        )
        session.add(short_url)
        await session.commit()
    
    response = await client.get("/db123", follow_redirects=False)
    
    assert response.status_code == 301
    assert response.headers["location"] == "https://example.com/database"
    
    # Verify Redis cache was backfilled (RedisCache uses setex)
    mock_redis.setex.assert_called()


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient, mock_redis):
    """Test redirect when short code is not found."""
    # Mock Redis to return None (cache miss)
    mock_redis.get = AsyncMock(return_value=None)
    
    response = await client.get("/nonexistent", follow_redirects=False)
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


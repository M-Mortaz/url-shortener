"""Integration tests for the URL shortener service."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.db.models import ShortURL


@pytest.mark.asyncio
async def test_full_flow_create_and_redirect(client: AsyncClient, test_db, mock_redis):
    """Test the complete flow: create short URL and then redirect to it."""
    # Step 1: Create a short URL
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/full-flow-test"}
    )
    
    assert create_response.status_code == 200
    create_data = create_response.json()
    short_code = create_data["short_code"]
    
    # Step 2: Mock Redis to return the URL (simulating cache)
    mock_redis.get = AsyncMock(return_value="https://example.com/full-flow-test")
    
    # Step 3: Redirect using the short code
    redirect_response = await client.get(f"/{short_code}", follow_redirects=False)
    
    assert redirect_response.status_code == 301
    assert redirect_response.headers["location"] == "https://example.com/full-flow-test"
    
    # Verify the short code matches
    assert short_code == "test123"  # From mock_id_generator


@pytest.mark.asyncio
async def test_multiple_short_urls(client: AsyncClient, test_db, mock_redis):
    """Test creating multiple short URLs with different original URLs."""
    urls = [
        "https://example.com/url1",
        "https://example.com/url2",
        "https://example.com/url3"
    ]
    
    short_codes = []
    for url in urls:
        response = await client.post("/shorten", json={"original_url": url})
        assert response.status_code == 200
        data = response.json()
        short_codes.append(data["short_code"])
        assert data["original_url"] == url
    
    # All should have the same short_code from mock (in real scenario they'd be different)
    # But we verify the structure is correct
    assert len(short_codes) == 3
    assert all(code == "test123" for code in short_codes)  # All use mock generator


@pytest.mark.asyncio
async def test_redirect_preserves_query_params(client: AsyncClient, mock_redis):
    """Test that redirect preserves the original URL structure."""
    original_url = "https://example.com/path?param1=value1&param2=value2"
    mock_redis.get = AsyncMock(return_value=original_url)
    
    response = await client.get("/test123", follow_redirects=False)
    
    assert response.status_code == 301
    assert response.headers["location"] == original_url


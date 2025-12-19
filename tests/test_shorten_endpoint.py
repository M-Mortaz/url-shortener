"""Tests for POST /shorten endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_short_url_success(client: AsyncClient):
    """Test successful creation of a short URL."""
    response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/very/long/url/path"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "short_code" in data
    assert "short_url" in data
    assert "original_url" in data
    assert data["original_url"] == "https://example.com/very/long/url/path"
    assert data["short_code"] == "test123"  # From mock_id_generator
    assert data["short_url"].endswith("/test123")


@pytest.mark.asyncio
async def test_create_short_url_missing_url(client: AsyncClient):
    """Test creating short URL with missing original_url."""
    response = await client.post("/shorten", json={})
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_short_url_invalid_url(client: AsyncClient):
    """Test creating short URL with invalid URL format."""
    response = await client.post(
        "/shorten",
        json={"original_url": "not-a-valid-url"}
    )
    
    assert response.status_code == 422  # Validation error


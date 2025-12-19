import asyncio
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import HttpUrl, BaseModel
from typing import Union

from app.db.session import get_session
from app.db.models import ShortURL
from app.core.id_service import get_id_generator
from app.core.redis_client import get_redis_client, RedisCache
from app.core.analytics import get_analytics_publisher
from app.core.setting import settings

router = APIRouter()


class ShortenRequest(BaseModel):
    original_url: HttpUrl


@router.post("/shorten")
async def create_short_url(
    request: ShortenRequest = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a short URL from a long URL.
    
    Generates a Snowflake ID, encodes it to Base62, and stores the mapping
    in both PostgreSQL and Redis cache.
    
    Accepts both JSON and form-encoded requests:
    - JSON: {"original_url": "https://example.com"}
    - Form: original_url=https://example.com
    """
    # Get URL from request body
    if not request or not request.original_url:
        raise HTTPException(status_code=400, detail="original_url is required")
    
    url_to_shorten = request.original_url
    
    # Generate Snowflake ID and encode to Base62
    id_generator = get_id_generator()
    snowflake_id = id_generator.generate()
    short_code = id_generator.generate_short_code()
    
    # Create ShortURL record
    short_url = ShortURL(
        snowflake_id=snowflake_id,
        original_url=str(url_to_shorten),
        short_code=short_code
    )
    
    # Save to database
    session.add(short_url)
    await session.commit()
    await session.refresh(short_url)
    
    # Cache in Redis
    redis_client = await get_redis_client()
    cache = RedisCache(redis_client)
    await cache.set(short_code, str(url_to_shorten))
    
    # Return short URL
    short_url_full = f"{settings.BASE_URL.rstrip('/')}/{short_code}"
    
    return {
        "short_code": short_code,
        "short_url": short_url_full,
        "original_url": str(url_to_shorten)
    }


@router.get(
    "/{short_code}",
    response_class=RedirectResponse,
    status_code=301,
    responses={
        301: {
            "description": "Permanent redirect to the original URL",
            "headers": {
                "Location": {
                    "description": "The original URL to redirect to",
                    "schema": {"type": "string", "format": "uri"}
                }
            }
        },
        404: {
            "description": "Short code not found",
            "content": {
                "application/json": {
                    "schema": {"type": "object", "properties": {"detail": {"type": "string"}}}
                }
            }
        }
    }
)
async def redirect_to_url(
    short_code: str,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Redirect to the original URL.
    
    This endpoint performs a permanent redirect (301) to the original URL associated with the short code.
    
    **Note for Swagger UI users:**
    - Swagger UI will automatically follow the redirect and show the final destination
    - To test the redirect behavior, use a browser or curl with `-L` flag
    - Example: `curl -L http://localhost:8000/abc123`
    
    **Performance optimizations:**
    - Redis cache-first lookup for minimal latency
    - Falls back to PostgreSQL on cache miss
    - Automatically backfills Redis cache
    
    **Analytics:**
    - Publishes click event to RabbitMQ asynchronously (non-blocking)
    - Event includes: short_code, timestamp, user_agent, IP address, referrer
    - Events are consumed by Event Consumer service and stored in ClickHouse
    """
    # Try Redis cache first (fast path)
    redis_client = await get_redis_client()
    cache = RedisCache(redis_client)
    original_url = await cache.get(short_code)
    
    if original_url:
        # Cache hit - publish analytics asynchronously
        analytics = await get_analytics_publisher()
        if analytics:
            # Fire and forget - don't await to avoid blocking redirect
            asyncio.create_task(
                analytics.publish_click_event(short_code, request, original_url)
            )
        
        return RedirectResponse(url=original_url, status_code=301)
    
    # Cache miss - query database
    statement = select(ShortURL).where(ShortURL.short_code == short_code)
    result = await session.exec(statement)
    short_url = result.first()
    
    if not short_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    original_url = short_url.original_url
    
    # Backfill Redis cache
    await cache.set(short_code, original_url)
    
    # Publish analytics asynchronously
    analytics = await get_analytics_publisher()
    if analytics:
        asyncio.create_task(
            analytics.publish_click_event(short_code, request, original_url)
        )
    
    return RedirectResponse(url=original_url, status_code=301)

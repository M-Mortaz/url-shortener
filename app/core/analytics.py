"""RabbitMQ event publisher for async analytics."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

import aio_pika
from aio_pika import Connection, Channel, Exchange
from fastapi import Request

from app.core.setting import settings

__all__ = ["AnalyticsPublisher", "get_analytics_publisher", "analytics_publisher"]

logger = logging.getLogger(__name__)

# Global analytics publisher instance
analytics_publisher: Optional["AnalyticsPublisher"] = None


class AnalyticsPublisher:
    """
    Publishes click events to RabbitMQ for async analytics processing.
    
    Events are published asynchronously and do not block the redirect path.
    """
    
    def __init__(self, connection: Connection, channel: Channel, exchange: Exchange):
        """
        Initialize the analytics publisher.
        
        Args:
            connection: RabbitMQ connection
            channel: RabbitMQ channel
            exchange: RabbitMQ exchange for routing
        """
        self.connection = connection
        self.channel = channel
        self.exchange = exchange
    
    async def publish_click_event(
        self,
        short_code: str,
        request: Request,
        original_url: str
    ) -> None:
        """
        Publish a click event to RabbitMQ.
        
        This method is non-blocking and will not raise exceptions that
        could affect the redirect response.
        
        Args:
            short_code: Short code that was clicked
            request: FastAPI request object for metadata
            original_url: Original URL that was redirected to
        """
        try:
            # Extract request metadata
            user_agent = request.headers.get("user-agent", "")
            ip_address = request.client.host if request.client else ""
            referrer = request.headers.get("referer", "")
            
            # Create event payload
            event = {
                "short_code": short_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_agent": user_agent,
                "ip_address": ip_address,
                "referrer": referrer,
                "original_url": original_url,
            }
            
            # Publish to RabbitMQ
            message_body = json.dumps(event).encode()
            
            await self.exchange.publish(
                aio_pika.Message(
                    message_body,
                    content_type="application/json",
                ),
                routing_key=settings.RABBITMQ_QUEUE,
            )
            
            logger.debug(f"Published click event for short_code: {short_code}")
        
        except Exception as e:
            # Log but don't raise - analytics failures should not affect redirects
            logger.warning(
                f"Failed to publish click event for {short_code}: {e}",
                exc_info=True
            )
    
    async def close(self) -> None:
        """Close the RabbitMQ connection."""
        try:
            await self.channel.close()
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}", exc_info=True)


async def get_analytics_publisher() -> Optional[AnalyticsPublisher]:
    """
    Get or create the global analytics publisher.
    
    Returns:
        AnalyticsPublisher instance, or None if RabbitMQ is unavailable
    """
    global analytics_publisher
    
    if analytics_publisher is None:
        try:
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await connection.channel()
            
            # Declare exchange
            exchange = await channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            queue = await channel.declare_queue(
                settings.RABBITMQ_QUEUE,
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key=settings.RABBITMQ_QUEUE)
            
            analytics_publisher = AnalyticsPublisher(connection, channel, exchange)
            logger.info("Analytics publisher initialized")
        
        except Exception as e:
            logger.error(
                f"Failed to initialize analytics publisher: {e}. "
                "Analytics will be disabled.",
                exc_info=True
            )
            analytics_publisher = None
    
    return analytics_publisher


async def close_analytics_publisher() -> None:
    """Close the analytics publisher connection."""
    global analytics_publisher
    
    if analytics_publisher:
        await analytics_publisher.close()
        analytics_publisher = None


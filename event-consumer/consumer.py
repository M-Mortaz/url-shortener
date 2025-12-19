"""
Event Consumer Service

Consumes click events from RabbitMQ and writes them to ClickHouse.
Pure Python asyncio implementation without ORM.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

import aio_pika
from aio_pika import Connection, IncomingMessage
from aiochclient import ChClient as ClickHouseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "url_shortener")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "click_events")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "url_shortener")
# Don't set user/password by default - let ClickHouse use defaults
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# Log configuration for debugging (after logger is configured)
logger.info(f"ClickHouse configuration: host={CLICKHOUSE_HOST}, port={CLICKHOUSE_PORT}, database={CLICKHOUSE_DATABASE}")


async def ensure_clickhouse_table(client: ClickHouseClient) -> None:
    """
    Ensure the click_events table exists in ClickHouse.
    
    Creates the table if it doesn't exist with the following schema:
    - short_code: String
    - timestamp: DateTime
    - user_agent: String
    - ip_address: String
    - referrer: String
    - original_url: String
    """
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DATABASE}.click_events (
        short_code String,
        timestamp DateTime,
        user_agent String,
        ip_address String,
        referrer String,
        original_url String
    ) ENGINE = MergeTree()
    ORDER BY (short_code, timestamp)
    """
    
    try:
        await client.execute(create_table_query)
        logger.info(f"ClickHouse table '{CLICKHOUSE_DATABASE}.click_events' ensured")
    except Exception as e:
        logger.error(f"Failed to create ClickHouse table: {e}", exc_info=True)
        raise


async def insert_click_event(client: ClickHouseClient, event: Dict[str, Any]) -> None:
    """
    Insert a click event into ClickHouse.
    
    Args:
        client: ClickHouse client
        event: Event dictionary with click event data
    """
    try:
        # Parse timestamp from ISO format and convert to ClickHouse DateTime format
        from datetime import datetime
        timestamp_str = event["timestamp"].replace("Z", "+00:00")
        timestamp_dt = datetime.fromisoformat(timestamp_str)
        # Format as string in ClickHouse DateTime format: 'YYYY-MM-DD HH:MM:SS'
        # ClickHouse DateTime doesn't support microseconds, so we truncate them
        timestamp_clickhouse = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Escape single quotes in string values for SQL safety
        def escape_sql_string(s: str) -> str:
            return s.replace("'", "''")
        
        # Prepare values with proper escaping
        short_code = escape_sql_string(event.get("short_code", ""))
        user_agent = escape_sql_string(event.get("user_agent", ""))
        ip_address = escape_sql_string(event.get("ip_address", ""))
        referrer = escape_sql_string(event.get("referrer", ""))
        original_url = escape_sql_string(event.get("original_url", ""))
        
        # Use raw SQL INSERT with properly formatted values
        # ClickHouse expects DateTime as string in format 'YYYY-MM-DD HH:MM:SS'
        insert_query = f"""
        INSERT INTO {CLICKHOUSE_DATABASE}.click_events 
        (short_code, timestamp, user_agent, ip_address, referrer, original_url) 
        VALUES 
        ('{short_code}', '{timestamp_clickhouse}', '{user_agent}', '{ip_address}', '{referrer}', '{original_url}')
        """
        
        # Execute the insert query
        await client.execute(insert_query)
        
        logger.debug(f"Inserted click event for short_code: {event.get('short_code')}")
    
    except Exception as e:
        logger.error(f"Failed to insert click event: {e}", exc_info=True)
        logger.error(f"Event data: {event}")
        raise


async def process_message(
    message: IncomingMessage,
    clickhouse_client: ClickHouseClient
) -> None:
    """
    Process a single message from RabbitMQ.
    
    Args:
        message: RabbitMQ incoming message
        clickhouse_client: ClickHouse client for database operations
    """
    async with message.process():
        try:
            # Parse JSON message
            event_data = json.loads(message.body.decode())
            logger.debug(f"Received event: {event_data.get('short_code')}")
            
            # Insert into ClickHouse
            await insert_click_event(clickhouse_client, event_data)
            
            logger.info(f"Successfully processed click event for: {event_data.get('short_code')}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            logger.error(f"Message body: {message.body.decode()}")
            # Message will be rejected and sent to dead letter queue if configured
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Re-raise to reject message (will be retried or sent to DLQ)
            raise


async def consume_events() -> None:
    """
    Main consumer loop that connects to RabbitMQ and ClickHouse,
    then consumes messages and writes them to ClickHouse.
    """
    rabbitmq_connection: Connection | None = None
    clickhouse_client: ClickHouseClient | None = None
    
    try:
        # Connect to ClickHouse
        logger.info("Connecting to ClickHouse...")
        # Construct URL - default ClickHouse allows passwordless access
        clickhouse_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
        
        # Build client kwargs - don't pass user/password unless explicitly set
        client_kwargs = {
            "url": clickhouse_url,
            "database": CLICKHOUSE_DATABASE,
        }
        
        # Only add user if explicitly provided
        if CLICKHOUSE_USER:
            client_kwargs["user"] = CLICKHOUSE_USER
        # Only add password if explicitly provided
        if CLICKHOUSE_PASSWORD:
            client_kwargs["password"] = CLICKHOUSE_PASSWORD
        
        logger.info(f"Connecting to ClickHouse with URL: {clickhouse_url}, database: {CLICKHOUSE_DATABASE}")
        clickhouse_client = ClickHouseClient(**client_kwargs)
        
        # Ensure table exists
        await ensure_clickhouse_table(clickhouse_client)
        logger.info("ClickHouse connection established")
        
        # Connect to RabbitMQ
        logger.info("Connecting to RabbitMQ...")
        rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
        logger.info("RabbitMQ connection established")
        
        # Create channel
        channel = await rabbitmq_connection.channel()
        
        # Declare exchange (should already exist, but ensure it)
        exchange = await channel.declare_exchange(
            RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Declare queue (should already exist, but ensure it)
        queue = await channel.declare_queue(
            RABBITMQ_QUEUE,
            durable=True
        )
        
        # Bind queue to exchange
        await queue.bind(exchange, routing_key=RABBITMQ_QUEUE)
        
        logger.info(f"Consuming messages from queue: {RABBITMQ_QUEUE}")
        logger.info("Event consumer started. Press CTRL+C to stop.")
        
        # Start consuming messages
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_message(message, clickhouse_client)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down...")
    
    except Exception as e:
        logger.error(f"Fatal error in consumer: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Cleanup connections
        if clickhouse_client:
            await clickhouse_client.close()
            logger.info("ClickHouse connection closed")
        
        if rabbitmq_connection:
            await rabbitmq_connection.close()
            logger.info("RabbitMQ connection closed")
        
        logger.info("Event consumer stopped")


def main() -> None:
    """Entry point for the event consumer."""
    try:
        asyncio.run(consume_events())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")


if __name__ == "__main__":
    main()


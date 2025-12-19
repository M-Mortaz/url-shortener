# Event Consumer Service

Pure Python asyncio service that consumes click events from RabbitMQ and writes them to ClickHouse.

## Overview

This service is part of the URL Shortener architecture:
- **URL Shortener FastAPI**: Publishes click events to RabbitMQ
- **Event Consumer** (this service): Consumes events and writes to ClickHouse
- **Analytics FastAPI**: Queries ClickHouse for statistics

## Features

- Pure Python asyncio implementation
- No ORM - direct ClickHouse inserts
- Automatic table creation
- Error handling and logging
- Graceful shutdown

## Installation

```bash
cd event-consumer
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:

```bash
# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=url_shortener
RABBITMQ_QUEUE=click_events

# ClickHouse Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=url_shortener
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
```

## Usage

```bash
python consumer.py
```

The consumer will:
1. Connect to ClickHouse and ensure the table exists
2. Connect to RabbitMQ
3. Start consuming messages from the queue
4. Insert each event into ClickHouse

## ClickHouse Table Schema

The service automatically creates the following table:

```sql
CREATE TABLE IF NOT EXISTS url_shortener.click_events (
    short_code String,
    timestamp DateTime,
    user_agent String,
    ip_address String,
    referrer String,
    original_url String
) ENGINE = MergeTree()
ORDER BY (short_code, timestamp)
```

## Event Schema

Events consumed from RabbitMQ should match this JSON structure:

```json
{
  "short_code": "abc123",
  "timestamp": "2024-01-01T12:00:00Z",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1",
  "referrer": "https://example.com",
  "original_url": "https://example.com/very/long/url/path"
}
```

## Running with Docker

You can run this as a separate container in your docker-compose setup:

```yaml
event-consumer:
  build:
    context: ./event-consumer
    dockerfile: Dockerfile
  environment:
    RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
    RABBITMQ_EXCHANGE: url_shortener
    RABBITMQ_QUEUE: click_events
    CLICKHOUSE_HOST: clickhouse
    CLICKHOUSE_PORT: 8123
    CLICKHOUSE_DATABASE: url_shortener
    CLICKHOUSE_USER: default
    CLICKHOUSE_PASSWORD: ""
  depends_on:
    - rabbitmq
    - clickhouse
```

## Error Handling

- **JSON Parse Errors**: Logged and message is rejected
- **ClickHouse Errors**: Logged and message is rejected (will be retried or sent to DLQ)
- **Connection Errors**: Service will exit with error code

## Logging

The service logs at INFO level by default. Set `LOG_LEVEL` environment variable to change:

```bash
LOG_LEVEL=DEBUG python consumer.py
```

## Scaling

Multiple instances of this consumer can run simultaneously. RabbitMQ will distribute messages across consumers using round-robin.


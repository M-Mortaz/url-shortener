# Analytics Service

Litestar-based web application that serves analytics and aggregated statistics from ClickHouse.

## Overview

This service is part of the URL Shortener architecture:
- **URL Shortener FastAPI**: Publishes click events to RabbitMQ
- **Event Consumer**: Consumes events and writes to ClickHouse
- **Analytics Service** (this service): Queries ClickHouse and serves statistics

## Features

- Litestar framework (high-performance async web framework)
- ClickHouse integration for analytics queries
- Aggregated statistics endpoints
- Health check endpoint

## Installation

```bash
cd analytics-service
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:

```bash
# ClickHouse Configuration (same as event-consumer)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=url_shortener
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
```

## Usage

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## API Endpoints

### GET /stats/{short_code}

Returns aggregated statistics for a short URL.

**Response:**
```json
{
  "short_code": "abc123",
  "total_clicks": 1234,
  "unique_visitors": 890,
  "last_clicked": "2024-01-15T10:30:00Z",
  "clicks_by_day": [
    {"date": "2024-01-15", "clicks": 45},
    {"date": "2024-01-14", "clicks": 32}
  ],
  "top_referrers": [
    {"referrer": "https://example.com", "clicks": 120},
    {"referrer": "https://google.com", "clicks": 80}
  ]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "analytics"
}
```

## Running with Docker

```bash
docker build -t analytics-service .
docker run -p 8001:8001 \
  -e CLICKHOUSE_HOST=clickhouse \
  -e CLICKHOUSE_DATABASE=url_shortener \
  analytics-service
```

## Integration with Nginx

Nginx should route `GET /stats/*` requests to this service:

```nginx
location /stats/ {
    proxy_pass http://analytics-service:8001;
}
```

All other requests go to the URL Shortener FastAPI service.


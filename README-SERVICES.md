# Services Overview

This project consists of three main services working together:

## 1. URL Shortener Service (FastAPI)

**Location:** `app/`  
**Port:** 8000  
**Framework:** FastAPI

### Responsibilities:
- Create short URLs (`POST /shorten`)
- Redirect users (`GET /{short_code}`)
- Publish click events to RabbitMQ

### Dependencies:
- PostgreSQL (URL storage)
- Redis (caching)
- RabbitMQ (event publishing)

## 2. Event Consumer Service

**Location:** `event-consumer/`  
**Framework:** Pure Python asyncio

### Responsibilities:
- Consume click events from RabbitMQ
- Write events to ClickHouse (append-only)

### Dependencies:
- RabbitMQ (consume events)
- ClickHouse (write events)

## 3. Analytics Service (Litestar)

**Location:** `analytics-service/`  
**Port:** 8001  
**Framework:** Litestar

### Responsibilities:
- Serve analytics and statistics (`GET /stats/{short_code}`)
- Query ClickHouse for aggregated data

### Dependencies:
- ClickHouse (read-only queries)

## Service Communication Flow

```
Client Request
    ↓
Nginx (Routes /stats/* to Analytics, others to URL Shortener)
    ↓
┌─────────────────┬──────────────────┐
│ URL Shortener   │  Analytics Svc   │
│   (FastAPI)     │   (Litestar)     │
└────────┬────────┴────────┬─────────┘
         │                 │
         │                 │
    RabbitMQ          ClickHouse
         │                 ↑
         │                 │
    Event Consumer ────────┘
```

## Running Services

### With Docker Compose (All Services)

```bash
docker compose up -d
```

### Individual Services

```bash
# URL Shortener
cd app
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Event Consumer
cd event-consumer
python consumer.py

# Analytics Service
cd analytics-service
python main.py
```

## Service URLs

- **URL Shortener API:** http://localhost:8000
- **Analytics API:** http://localhost:8001
- **RabbitMQ Management:** http://localhost:15672 (guest/guest)
- **ClickHouse HTTP:** http://localhost:8123

## Environment Variables

Each service uses environment variables. See:
- `.env` - Main configuration (for URL Shortener)
- `event-consumer/.env.example` - Event Consumer config
- `analytics-service/.env.example` - Analytics Service config

## Health Checks

- URL Shortener: `GET http://localhost:8000/docs`
- Analytics Service: `GET http://localhost:8001/health`
- Event Consumer: Check logs for connection status


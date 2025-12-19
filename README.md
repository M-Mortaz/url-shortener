# 🔗 URL Shortener – Production-Ready Microservices Architecture

A scalable, production-ready URL shortening service built with **FastAPI**, **SQLModel**, **Alembic**, and modern microservices architecture. This system demonstrates enterprise-level patterns including async event processing, distributed ID generation, caching strategies, and analytics aggregation.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture Overview](#-architecture-overview)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Data Flow](#-data-flow)
- [Services Description](#-services-description)
- [Getting Started](#-getting-started)
- [Running Tests](#-running-tests)
- [Load Testing](#-load-testing)
- [Deployment](#-deployment)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)

---

## 🧩 Features

### Core Functionality
- **URL Shortening**: Create short URLs from long URLs (`POST /shorten`)
- **URL Redirection**: Permanent redirects (301) to original URLs (`GET /{short_code}`)
- **Analytics**: Real-time click statistics and analytics (`GET /stats/{short_code}`)
- **Caching**: Redis-based caching for sub-millisecond URL lookups
- **Event Processing**: Asynchronous event processing via RabbitMQ
- **Distributed IDs**: Snowflake ID generation for unique, distributed-safe short codes

### Technical Features
- **Microservices Architecture**: Separated concerns with independent services
- **Async Processing**: Non-blocking analytics event publishing
- **Database Migrations**: Alembic for schema versioning
- **Load Testing**: Locust-based performance testing suite
- **Comprehensive Testing**: Async unit and integration tests
- **API Documentation**: OpenAPI/Swagger specification
- **Health Checks**: Service health monitoring
- **Logging**: Request logging middleware

---

## 🏗️ Architecture Overview

This system follows a **microservices architecture** with clear separation of concerns:

1. **URL Shortener Service** (FastAPI) - Core business logic
2. **Analytics Service** (Litestar) - Analytics and statistics
3. **Event Consumer** - Background event processing
4. **Nginx** - Reverse proxy and request routing
5. **PostgreSQL** - Primary transactional database
6. **Redis** - In-memory cache layer
7. **RabbitMQ** - Message queue for async events
8. **ClickHouse** - Analytics data warehouse

---

## 💻 Technology Stack

### Backend Frameworks
- **FastAPI** (v0.104+) - Modern, fast Python web framework for URL Shortener service
- **Litestar** - High-performance framework for Analytics service
- **SQLModel** - SQL database ORM built on SQLAlchemy and Pydantic
- **Alembic** - Database migration tool

### Databases & Storage
- **PostgreSQL 15** - Primary relational database for URL mappings
- **Redis 7** - In-memory cache for fast URL lookups
- **ClickHouse** - Column-oriented database for analytics data

### Message Queue
- **RabbitMQ 3** - Message broker for asynchronous event processing

### Infrastructure
- **Docker & Docker Compose** - Containerization and orchestration
- **Nginx** - Reverse proxy and load balancer
- **Python 3.14** - Runtime environment

### Testing & Monitoring
- **Pytest** - Testing framework
- **Pytest-asyncio** - Async test support
- **Locust** - Load testing framework
- **httpx** - Async HTTP client for testing

### Key Libraries
- **asyncpg** - Async PostgreSQL driver
- **aio-pika** - Async RabbitMQ client
- **aiochclient** - Async ClickHouse client
- **redis[hiredis]** - Redis client with performance optimizations

---

## 🎯 System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Requests                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Nginx (80)    │    
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │  URL Shortener       │   │  Analytics Service   │
    │  Service (8000)      │   │  (8001)              │
    │  FastAPI             │   │  Litestar            │
    └──────────┬───────────┘   └──────────┬───────────┘
               │                          │
    ┌──────────┴────────────┐             │
    │          │            │             │
    ▼          ▼            ▼             |
┌──────────┐ ┌──────┐   ┌─────────┐       |
│PostgreSQL│ │Redis │   │ RabbitMQ│       |
│  (5432)  │ │(6379)│   │  (5672) │       |
└──────────┘ └──────┘   └────┬────┘       |
                             │            │
                             ▼            │
                      ┌──────────────┐    │
                      │Event Consumer│    │
                      │  (Background)│    |
                      └──────────────┘    |
                              |           ▼
                              |     ┌──────────┐
                              └───▶ │ClickHouse│
                                    │  (8123)  │
                                    └──────────┘
```

### Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    URL Creation Flow                        │
└─────────────────────────────────────────────────────────────┘

Client → POST /shorten
    ↓
Nginx → URL Shortener Service
    ↓
1. Generate Snowflake ID → Base62 encode → short_code
2. Store in PostgreSQL (ShortURL table)
3. Cache in Redis (TTL: 24h)
4. Return short_url to client

┌─────────────────────────────────────────────────────────────┐
│                    URL Redirection Flow                      │
└─────────────────────────────────────────────────────────────┘

Client → GET /{short_code}
    ↓
Nginx → URL Shortener Service
    ↓
1. Check Redis cache (fast path)
   ├─ Cache HIT → Return 301 redirect
   └─ Cache MISS → Query PostgreSQL
                    ├─ Found → Cache in Redis → Return 301 redirect
                    └─ Not Found → Return 404
2. Publish click event to RabbitMQ (async, non-blocking)
    ↓
Event Consumer → Store in ClickHouse

┌─────────────────────────────────────────────────────────────┐
│                    Analytics Flow                            │
└─────────────────────────────────────────────────────────────┘

Client → GET /stats/{short_code}
    ↓
Nginx → Analytics Service
    ↓
Query ClickHouse
    ├─ Aggregate click statistics
    ├─ Calculate unique visitors
    ├─ Get time-series data
    └─ Return JSON response
```

---

## 🔄 Data Flow

### 1. URL Creation Flow

```
┌────────┐
│ Client │
└───┬────┘
    │ POST /shorten {"original_url": "https://example.com/very/long/url"}
    ▼
┌────────┐
│ Nginx  │
└───┬────┘
    │ Route to URL Shortener Service
    ▼
┌──────────────────────┐
│ URL Shortener        │
│ Service (FastAPI)    │
└───┬──────────────────┘
    │
    ├─→ Generate Snowflake ID (64-bit)
    ├─→ Encode to Base62 → short_code
    │
    ├─→ PostgreSQL: INSERT INTO short_urls
    │   (snowflake_id, short_code, original_url)
    │
    └─→ Redis: SET short_url:{short_code} = original_url (TTL: 24h)
    │
    └─→ Return: {"short_code": "abc123", "short_url": "http://localhost/abc123"}
```

### 2. URL Redirection Flow

```
┌────────┐
│ Client │
└───┬────┘
    │ GET /abc123
    ▼
┌────────┐
│ Nginx  │
└───┬────┘
    │ Route to URL Shortener Service
    ▼
┌──────────────────────┐
│ URL Shortener        │
│ Service (FastAPI)    │
└───┬──────────────────┘
    │
    ├─→ Redis: GET short_url:abc123
    │   ├─ HIT → original_url found
    │   └─ MISS → Query PostgreSQL
    │              ├─ SELECT * FROM short_urls WHERE short_code = 'abc123'
    │              └─ Cache result in Redis
    │
    ├─→ Publish event to RabbitMQ (async, fire-and-forget)
    │   {
    │     "short_code": "abc123",
    │     "timestamp": "2024-01-15T10:30:00Z",
    │     "ip_address": "192.168.1.1",
    │     "user_agent": "Mozilla/5.0...",
    │     "referrer": "https://example.com"
    │   }
    │
    └─→ Return: 301 Redirect to original_url
```

### 3. Analytics Processing Flow

```
┌──────────────────────┐
│ Event Consumer       │
│ (Background Worker)  │
└───┬──────────────────┘
    │
    ├─→ RabbitMQ: Consume click events from queue
    │
    ├─→ ClickHouse: INSERT INTO click_events
    │   (
    │     short_code,
    │     timestamp,
    │     ip_address,
    │     user_agent,
    │     referrer
    │   )
    │
    └─→ Process events in batches for efficiency

┌────────┐
│ Client │
└───┬────┘
    │ GET /stats/abc123
    ▼
┌────────┐
│ Nginx  │
└───┬────┘
    │ Route to Analytics Service
    ▼
┌──────────────────────┐
│ Analytics Service    │
│ (Litestar)           │
└───┬──────────────────┘
    │
    └─▶ ClickHouse: Query aggregated statistics
        ├─ SELECT COUNT(*) as total_clicks
        ├─ SELECT COUNT(DISTINCT ip_address) as unique_visitors
        ├─ SELECT * FROM clicks_by_day WHERE short_code = 'abc123'
        └─ SELECT referrer, COUNT(*) FROM click_events GROUP BY referrer
```

---

## 🛠️ Services Description

### 1. URL Shortener Service (FastAPI)

**Location:** `app/`  
**Port:** 8000  
**Framework:** FastAPI  
**Python Version:** 3.14

#### Responsibilities
- Create short URLs from long URLs
- Redirect users to original URLs
- Manage URL mappings in PostgreSQL
- Cache URLs in Redis for fast lookups
- Publish click events to RabbitMQ

#### Endpoints
- `POST /shorten` - Create a short URL
- `GET /{short_code}` - Redirect to original URL (301)
- `GET /docs` - Interactive API documentation (Swagger UI)

#### Dependencies
- **PostgreSQL** - Primary database for URL storage
- **Redis** - Cache layer for fast lookups
- **RabbitMQ** - Event publishing for analytics

#### Key Features
- Snowflake ID generation for unique short codes
- Base62 encoding for URL-friendly short codes
- Redis cache-first lookup strategy
- Async event publishing (non-blocking)
- Connection pooling for database efficiency
- CORS enabled for Swagger UI

---

### 2. Analytics Service (Litestar)

**Location:** `analytics-service/`  
**Port:** 8001  
**Framework:** Litestar  
**Python Version:** 3.14

#### Responsibilities
- Serve analytics and statistics
- Query ClickHouse for aggregated data
- Provide real-time click statistics

#### Endpoints
- `GET /stats/{short_code}` - Get URL statistics
- `GET /health` - Health check endpoint

#### Dependencies
- **ClickHouse** - Analytics data warehouse (read-only)

#### Key Features
- Fast query performance with ClickHouse
- Aggregated statistics (total clicks, unique visitors)
- Time-series data (clicks by day)
- Top referrers analysis
- CORS enabled for cross-origin requests

---

### 3. Event Consumer Service

**Location:** `event-consumer/`  
**Framework:** Pure Python asyncio  
**Python Version:** 3.14

#### Responsibilities
- Consume click events from RabbitMQ
- Write events to ClickHouse
- Process events asynchronously

#### Dependencies
- **RabbitMQ** - Message queue (consumer)
- **ClickHouse** - Analytics database (writer)

#### Key Features
- Async event processing
- Batch processing for efficiency
- Automatic reconnection on failures
- Error handling and logging

---

### 4. Nginx Reverse Proxy

**Location:** `nginx-config/`  
**Port:** 80  
**Image:** nginx:alpine

#### Responsibilities
- Route requests to appropriate services
- Load balancing (ready for horizontal scaling)
- SSL termination (production ready)

#### Routing Rules
- `/stats/*` → Analytics Service (port 8001)
- All other routes → URL Shortener Service (port 8000)

#### Key Features
- Request routing based on path
- Health check integration
- Proxy headers configuration
- Timeout management

---

### 5. PostgreSQL Database

**Image:** postgres:15-alpine  
**Port:** 5432

#### Schema
- **short_urls** table:
  - `snowflake_id` (BIGINT, PRIMARY KEY) - Snowflake ID
  - `short_code` (VARCHAR, UNIQUE) - Base62 encoded short code
  - `original_url` (TEXT) - Original long URL
  - `created_at` (TIMESTAMP) - Creation timestamp

#### Features
- Connection pooling (20 connections, max 30)
- Health checks
- Persistent storage via Docker volumes

---

### 6. Redis Cache

**Image:** redis:7-alpine  
**Port:** 6379

#### Usage
- Cache key format: `short_url:{short_code}`
- TTL: 24 hours (86400 seconds)
- Cache-first lookup strategy
- Automatic backfill on cache miss

#### Features
- AOF (Append Only File) persistence
- Health checks
- In-memory storage for sub-millisecond lookups

---

### 7. RabbitMQ Message Queue

**Image:** rabbitmq:3-management-alpine  
**Ports:** 5672 (AMQP), 15672 (Management UI)

#### Configuration
- Exchange: `url_shortener`
- Queue: `click_events`
- Routing: Direct exchange

#### Features
- Management UI for monitoring
- Persistent queues
- Health checks
- Message durability

---

### 8. ClickHouse Analytics Database

**Image:** clickhouse/clickhouse-server:latest  
**Ports:** 8123 (HTTP), 9000 (Native)

#### Schema
- **click_events** table:
  - `short_code` (String)
  - `timestamp` (DateTime)
  - `ip_address` (String)
  - `user_agent` (String)
  - `referrer` (String)

#### Features
- Column-oriented storage for fast analytics
- High compression ratio
- Time-series optimized
- Aggregation-friendly queries

---

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository
- (Optional) Python 3.14+ for local development

### Quick Start with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/mahdimmr/url-shortener.git
cd url-shortener

# 2. Copy environment file
cp sample.env .env

# 3. Start all services
docker compose up -d

# 4. Wait for services to be ready (check logs)
docker compose logs -f

# 5. Access the application
# Main API: http://localhost/docs
# Analytics: http://localhost/stats/{short_code}
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Main API** | http://localhost | Nginx reverse proxy |
| **Swagger UI** | http://localhost/docs | Interactive API docs |
| **URL Shortener** | http://localhost:8000 | Direct access to FastAPI |
| **Analytics** | http://localhost:8001 | Direct access to Litestar |
| **RabbitMQ UI** | http://localhost:15672 | Management interface (guest/guest) |
| **ClickHouse** | http://localhost:8123 | HTTP interface |
| **Locust UI** | http://localhost:8089 | Load testing interface |

### Verify Installation

```bash
# Check all services are running
docker compose ps

# Test URL creation
curl -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'

# Test redirect (use short_code from above)
curl -L http://localhost/{short_code}

# Test analytics
curl http://localhost/stats/{short_code}
```

---

## 🧪 Running Tests

### Using Docker Compose (Recommended)

```bash
# Run all tests
docker compose --profile test run --rm test

# Run with verbose output
docker compose --profile test run --rm test pytest tests/ -v

# Run specific test file
docker compose --profile test run --rm test pytest tests/test_shorten_endpoint.py -v

# Run with coverage
docker compose --profile test run --rm test pytest tests/ --cov=app --cov-report=html
```

### Test Structure

- **`test_shorten_endpoint.py`** - POST /shorten endpoint tests
- **`test_redirect_endpoint.py`** - GET /{short_code} redirect tests
- **`test_integration.py`** - Full workflow integration tests

See [tests/README.md](tests/README.md) for detailed testing documentation.

---

## 📊 Load Testing

### Using Locust

```bash
# Start Locust UI
docker compose up -d locust

# Access Locust UI
open http://localhost:8089

# Select user class and run tests
# - CreateShortURLUser: Test URL creation
# - RedirectUser: Test redirects
# - StatsUser: Test analytics
```

### Providing Custom Short Codes

Edit `docker-compose.yml`:

```yaml
locust:
  environment:
    LOCUST_SHORT_CODES: "abc123,def456,ghi789"
```

Then restart: `docker compose restart locust`

See [benchmark/README.md](benchmark/README.md) for comprehensive load testing guide.

---

## 🐳 Deployment

### Production Deployment

```bash
# 1. Set production environment variables
cp sample.env .env
# Edit .env with production values

# 2. Build and start services
docker compose up -d --build

# 3. Run database migrations
docker compose exec url-shortener alembic upgrade head

# 4. Check service health
docker compose ps
docker compose logs -f
```

### Environment Variables

Key environment variables (see `sample.env`):

- `PG_DSN` - PostgreSQL connection string
- `REDIS_URL` - Redis connection URL
- `RABBITMQ_URL` - RabbitMQ connection URL
- `BASE_URL` - Base URL for short link generation
- `WORKER_ID_LEASE_TTL` - Worker ID lease time-to-live

### Scaling Services

```bash
# Scale URL Shortener service (example)
docker compose up -d --scale url-shortener=3

# Scale Event Consumer (example)
docker compose up -d --scale event-consumer=2
```

---

## ⚙️ Configuration

### Database Connection Pool

Configured in `app/core/settings.py`:

- `DB_POOL_SIZE`: 20 (default connections)
- `DB_MAX_OVERFLOW`: 10 (additional connections)
- `DB_POOL_TIMEOUT`: 30 seconds
- `DB_POOL_RECYCLE`: 3600 seconds (1 hour)

### Redis Cache

- TTL: 24 hours (86400 seconds)
- Key prefix: `short_url:`
- Persistence: AOF enabled

### Worker ID Management

- Max Worker IDs: 1023 (10 bits)
- Lease TTL: 60 seconds
- Renewal interval: 30 seconds

---

## 🔧 Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker compose logs [service-name]

# Check service status
docker compose ps

# Restart a specific service
docker compose restart [service-name]
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose exec postgres pg_isready -U urlshortener

# Check connection string in .env
cat .env | grep PG_DSN
```

### Redis Connection Issues

```bash
# Test Redis connection
docker compose exec redis redis-cli ping

# Check Redis logs
docker compose logs redis
```

### RabbitMQ Issues

```bash
# Check RabbitMQ status
docker compose exec rabbitmq rabbitmq-diagnostics ping

# Access management UI
open http://localhost:15672
```

### ClickHouse Issues

```bash
# Test ClickHouse connection
curl http://localhost:8123/ping

# Check ClickHouse logs
docker compose logs clickhouse
```

### Common Issues

1. **Port already in use**: Stop conflicting services or change ports in `docker-compose.yml`
2. **Database migration errors**: Run `docker compose exec url-shortener alembic upgrade head`
3. **Cache not working**: Check Redis is running and connection string is correct
4. **Events not processing**: Check RabbitMQ and Event Consumer logs

---

## 📁 Project Structure

```
url-shortener/
├── app/                          # URL Shortener Service (FastAPI)
│   ├── api/
│   │   └── endpoints.py         # API route handlers
│   ├── core/
│   │   ├── analytics.py         # RabbitMQ event publisher
│   │   ├── id_generator.py      # Snowflake ID generator
│   │   ├── id_service.py        # ID generator singleton
│   │   ├── redis_client.py      # Redis client wrapper
│   │   ├── settings.py          # Configuration (Pydantic)
│   │   └── worker_id.py         # Worker ID management
│   ├── db/
│   │   ├── models.py            # SQLModel database models
│   │   └── session.py           # Database session management
│   ├── middleware/
│   │   └── logging.py           # Request logging middleware
│   └── main.py                  # FastAPI application entry point
│
├── analytics-service/            # Analytics Service (Litestar)
│   ├── main.py                  # Litestar application
│   └── requirements.txt         # Python dependencies
│
├── event-consumer/               # Event Consumer Service
│   ├── consumer.py              # RabbitMQ consumer
│   └── requirements.txt         # Python dependencies
│
├── benchmark/                    # Load Testing (Locust)
│   ├── locustfile.py            # Load test definitions
│   ├── Dockerfile               # Locust container
│   └── README.md                # Load testing guide
│
├── tests/                        # Unit and Integration Tests
│   ├── conftest.py              # Pytest fixtures
│   ├── test_shorten_endpoint.py # URL creation tests
│   ├── test_redirect_endpoint.py # Redirect tests
│   ├── test_integration.py      # Integration tests
│   └── README.md                # Testing documentation
│
├── migrations/                   # Database Migrations (Alembic)
│   ├── env.py                   # Alembic environment
│   ├── script.py.mako           # Migration template
│   └── versions/                # Migration files
│
├── nginx-config/                 # Nginx Configuration
│   └── nginx.conf                # Reverse proxy config
│
├── clickhouse-config/            # ClickHouse Configuration
│   └── users.xml                 # User settings
│
├── docker-compose.yml            # Docker Compose orchestration
├── Dockerfile                    # URL Shortener Dockerfile
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── alembic.ini                    # Alembic configuration
├── sample.env                    # Environment variables template
├── openapi.yaml                  # OpenAPI/Swagger specification
├── README.md                     # This file
└── README-SERVICES.md            # Detailed service documentation
```

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc
- **OpenAPI Spec**: http://localhost/openapi.json

### API Endpoints

#### Create Short URL

```http
POST /shorten
Content-Type: application/json

{
  "original_url": "https://example.com/very/long/url/path"
}
```

**Response:**
```json
{
  "short_code": "abc123",
  "short_url": "http://localhost/abc123",
  "original_url": "https://example.com/very/long/url/path"
}
```

#### Redirect to Original URL

```http
GET /{short_code}
```

**Response:** 301 Redirect to original URL

#### Get URL Statistics

```http
GET /stats/{short_code}
```

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

See [openapi.yaml](openapi.yaml) for complete API specification.

---

## 📚 Additional Documentation

- **[README-SERVICES.md](README-SERVICES.md)** - Detailed service documentation
- **[tests/README.md](tests/README.md)** - Testing guide and documentation
- **[benchmark/README.md](benchmark/README.md)** - Load testing guide
- **[openapi.yaml](openapi.yaml)** - OpenAPI/Swagger specification

---

## 🎯 Design Decisions

### Why Snowflake IDs?
- **Distributed-safe**: No coordination needed between instances
- **Time-ordered**: IDs contain timestamp information
- **Scalable**: Supports up to 1024 workers, 4096 IDs/ms per worker
- **URL-friendly**: Base62 encoding produces short, readable codes

### Why Separate Analytics Service?
- **Separation of Concerns**: Analytics queries don't impact main API performance
- **Independent Scaling**: Scale analytics separately based on query load
- **Technology Choice**: Litestar optimized for read-heavy workloads

### Why ClickHouse for Analytics?
- **Column-oriented**: Optimized for analytical queries
- **High Performance**: Fast aggregations and time-series queries
- **Compression**: Efficient storage for large volumes of click events
- **Scalability**: Handles billions of events efficiently

### Why RabbitMQ for Events?
- **Reliability**: Message persistence and delivery guarantees
- **Decoupling**: Analytics processing doesn't block URL redirection
- **Scalability**: Can handle high event volumes
- **Monitoring**: Built-in management UI for queue monitoring

---

## 🧠 Future Enhancements

- Custom short code support
- URL expiration dates
- Rate limiting and DDoS protection
- Authentication and authorization
- Admin dashboard
- URL preview/thumbnail generation
- QR code generation
- Bulk URL import/export
- Multi-tenant support
- Geographic analytics
- A/B testing for URLs

---

## 📝 License

This project is part of a technical interview process.

---

## 👥 Contributing

This is an interview project. For questions or feedback, please contact the repository owner.

---

**Built with ❤️ using FastAPI, SQLModel, and modern Python async patterns.**

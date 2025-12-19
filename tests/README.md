# Tests

This directory contains async unit and integration tests for the URL Shortener service.

## Running Tests

### Using Docker Compose (Recommended)

```bash
# Run all tests
docker compose --profile test run --rm test

# Run with verbose output
docker compose --profile test run --rm test pytest tests/ -v

# Run specific test file
docker compose --profile test run --rm test pytest tests/test_shorten_endpoint.py -v

# Run specific test
docker compose --profile test run --rm test pytest tests/test_shorten_endpoint.py::test_create_short_url_success -v

# Run with coverage
docker compose --profile test run --rm test pytest tests/ --cov=app --cov-report=html
```

### Inside Running Container

```bash
# Install test dependencies (first time only)
docker compose exec url-shortener pip install pytest-asyncio httpx aiosqlite -q

# Run all tests
docker compose exec url-shortener pytest tests/ -v

# Run specific test file
docker compose exec url-shortener pytest tests/test_shorten_endpoint.py -v
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_shorten_endpoint.py       # POST /shorten endpoint tests
├── test_redirect_endpoint.py      # GET /{short_code} redirect tests
└── test_integration.py            # Integration tests
```

## Test Files

### `test_shorten_endpoint.py`
Tests for the URL shortening endpoint:
- `test_create_short_url_success` - Successful URL creation
- `test_create_short_url_missing_url` - Missing URL validation
- `test_create_short_url_invalid_url` - Invalid URL format validation

### `test_redirect_endpoint.py`
Tests for the redirect endpoint:
- `test_redirect_with_cache_hit` - Redis cache hit scenario
- `test_redirect_with_cache_miss` - Database fallback scenario
- `test_redirect_not_found` - 404 for non-existent short codes

### `test_integration.py`
Integration tests for complete workflows:
- `test_full_flow_create_and_redirect` - Create → Redirect flow
- `test_multiple_short_urls` - Multiple URL creation
- `test_redirect_preserves_query_params` - URL structure preservation

## Test Configuration

- **`conftest.py`** - Contains async fixtures for:
  - Test database (in-memory SQLite)
  - Mock Redis client
  - Mock analytics publisher
  - Mock ID generator
  - Test HTTP client (httpx with ASGI transport)

- **`pytest.ini`** - Pytest configuration with async mode enabled

## Writing Tests

- Use `pytest` fixtures for test setup and teardown
- Mock external services (Redis, RabbitMQ, ClickHouse) for unit tests
- Use in-memory SQLite database for fast tests
- Follow the AAA pattern: Arrange, Act, Assert
- All tests use async/await with `@pytest.mark.asyncio`
- Use `httpx.AsyncClient` with `ASGITransport` for testing FastAPI endpoints

## Dependencies

Test dependencies (automatically installed in Docker):
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `httpx` - Async HTTP client for testing
- `aiosqlite` - Async SQLite driver for test database


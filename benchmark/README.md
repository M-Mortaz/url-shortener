# URL Shortener Load Testing with Locust

This directory contains Locust load tests for the URL Shortener service.

## 👥 User Class Selection

Each user class tests ONLY one endpoint:
- **`CreateShortURLUser`** - POST /shorten (create short URLs)
- **`RedirectUser`** - GET /{short_code} (redirect to URLs)  
- **`StatsUser`** - GET /stats/{short_code} (get analytics)

### How to Provide Custom Short Codes for Redirect/Stats Tests

For `RedirectUser` and `StatsUser`, you can provide your own short codes via the `LOCUST_SHORT_CODES` environment variable.

#### Method 1: Edit docker-compose.yml (Recommended)

Edit the `locust` service in `docker-compose.yml`:

```yaml
locust:
  environment:
    LOCUST_SHORT_CODES: "abc123,def456,ghi789"  # Your short codes here
```

**Format:** Comma-separated list of short codes (no spaces)

**Example:**
```yaml
environment:
  LOCUST_SHORT_CODES: "jdTIEyST97,jdTK9uwNmF,jdTwVNwJ7H"
```

Then restart:
```bash
docker compose restart locust
```

#### Method 2: Set Environment Variable When Starting

```bash
LOCUST_SHORT_CODES="abc123,def456,ghi789" docker compose up -d locust
```

### How to Run Tests by User Class

#### Via Locust UI (Simple Mode with --class-picker)

1. Open http://localhost:8089
2. You should see user class selection in the UI
3. Select the user class you want to test:
   - `CreateShortURLUser` - Test only URL creation
   - `RedirectUser` - Test only redirects (uses your custom short codes if provided)
   - `StatsUser` - Test only stats (uses your custom short codes if provided)
4. Set number of users and spawn rate
5. Start the test

**Note:** If `LOCUST_SHORT_CODES` is not set, `RedirectUser` and `StatsUser` will generate random short codes (may return 404).

## Running with Docker Compose (Recommended)

The Locust master and workers are configured in `docker-compose.yml`.

### Start Locust with 8 Workers

```bash
# Build and start Locust master + 8 workers
docker compose up --build --scale locust-worker=8 locust-master locust-worker

# Or start all services including Locust
docker compose up --scale locust-worker=8
```

Then open your browser to: **http://localhost:8089**

### Stop Locust

```bash
docker compose stop locust-master locust-worker
```

### View Logs

```bash
# Master logs
docker compose logs -f locust-master

# Worker logs
docker compose logs -f locust-worker
```

## Manual Installation (Local Testing)

```bash
pip install -r requirements.txt
```

Or install Locust globally:
```bash
pip install locust
```

## Running Tests Locally

### Basic Usage (Single Process)

Start Locust web UI:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Or test through Nginx:
```bash
locust -f locustfile.py --host=http://localhost
```

Then open your browser to: `http://localhost:8089`

### Distributed Mode (Master + Workers)

For higher load, run with multiple workers:

**Terminal 1 - Master (with UI):**
```bash
locust -f locustfile.py --master --host=http://localhost:8000
```

**Terminal 2-9 - Workers (8 workers):**
```bash
# Run this command 8 times in separate terminals
locust -f locustfile.py --worker --master-host=localhost
```

Then open your browser to: `http://localhost:8089`

### Command Line (Headless Mode)

Run without web UI:
```bash
# Run for 60 seconds with 10 users, spawn rate of 2 users/second
locust -f locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s

# Run with more users for stress testing
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m
```

### Advanced Options

```bash
# Run with specific user class (test endpoints separately)
locust -f locustfile.py CreateShortURLUser --host=http://localhost:8000 -u 50 -r 5
locust -f locustfile.py RedirectUser --host=http://localhost:8000 -u 50 -r 5
locust -f locustfile.py StatsUser --host=http://localhost:8000 -u 50 -r 5

# Provide short codes for redirect/stats testing
LOCUST_SHORT_CODES=abc123,def456,ghi789 locust -f locustfile.py RedirectUser --host=http://localhost:8000
LOCUST_SHORT_CODES=abc123,def456,ghi789 locust -f locustfile.py StatsUser --host=http://localhost:8000

# Save results to CSV
locust -f locustfile.py CreateShortURLUser --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m --csv=results

# Run with custom host and port
locust -f locustfile.py CreateShortURLUser --host=http://localhost:8000 --web-host=0.0.0.0 --web-port=8089
```

## Test Scenarios

Each user class tests ONLY one endpoint. You can select which user class to run in the Locust UI.

### CreateShortURLUser
Tests ONLY the **POST /shorten** endpoint:
- Creates short URLs with very simple URLs (e.g., https://example.com)
- **Select only this user class** to test URL creation performance separately
- No input required - generates simple URLs automatically

### RedirectUser
Tests ONLY the **GET /{short_code}** redirect endpoint:
- **Select only this user class** to test redirects separately
- You can provide short codes via `LOCUST_SHORT_CODES` environment variable
- Format: `LOCUST_SHORT_CODES=abc123,def456,ghi789`
- If not provided, generates random short codes (may return 404)

### StatsUser
Tests ONLY the **GET /stats/{short_code}** analytics endpoint:
- **Select only this user class** to test stats separately
- You can provide short codes via `LOCUST_SHORT_CODES` environment variable
- Format: `LOCUST_SHORT_CODES=abc123,def456,ghi789`
- If not provided, generates random short codes (may return 404)

## How to Run Separate Tests

### Step-by-Step Guide for Locust UI

1. **Open Locust UI:** Go to http://localhost:8089

2. **Select User Class:**
   - Look for the **"User classes"** section on the main page
   - You'll see checkboxes or a picker for:
     - `CreateShortURLUser`
     - `RedirectUser`
     - `StatsUser`
   - **IMPORTANT:** Uncheck all user classes EXCEPT the one you want to test
   - Or use the user class picker to select only one

3. **Set Test Parameters:**
   - **Number of users:** How many concurrent users (e.g., 10, 50, 100)
   - **Spawn rate:** Users per second (e.g., 2, 5, 10)
   - **Host:** Should be pre-filled with `http://nginx` (do not change)

4. **Start Test:**
   - Click **"Start Swarming"** button
   - Only the selected user class will run

### Test Scenarios

#### 1. Test Create Short URL Only:
- ✅ Check ONLY `CreateShortURLUser`
- ❌ Uncheck `RedirectUser` and `StatsUser`
- Set users and spawn rate
- Click "Start Swarming"
- **Result:** Only POST /shorten requests will be sent

#### 2. Test Redirect Only:
- ✅ Check ONLY `RedirectUser`
- ❌ Uncheck `CreateShortURLUser` and `StatsUser`
- (Optional) Set `LOCUST_SHORT_CODES` environment variable with your short codes
- Set users and spawn rate
- Click "Start Swarming"
- **Result:** Only GET /{short_code} redirect requests will be sent

#### 3. Test Stats Only:
- ✅ Check ONLY `StatsUser`
- ❌ Uncheck `CreateShortURLUser` and `RedirectUser`
- (Optional) Set `LOCUST_SHORT_CODES` environment variable with your short codes
- Set users and spawn rate
- Click "Start Swarming"
- **Result:** Only GET /stats/{short_code} requests will be sent

### Visual Guide

When you open the Locust UI, you should see something like:

```
┌─────────────────────────────────────┐
│  User classes:                       │
│  ☑ CreateShortURLUser               │  ← Uncheck if not testing
│  ☐ RedirectUser                      │  ← Check ONLY if testing redirects
│  ☐ StatsUser                         │  ← Check ONLY if testing stats
│                                     │
│  Number of users: [____]            │
│  Spawn rate: [____]                 │
│  Host: [http://nginx]               │
│                                     │
│  [Start Swarming]                   │
└─────────────────────────────────────┘
```

**Critical:** Make sure only ONE checkbox is checked at a time!

### Troubleshooting

**Problem:** All tests are running together
- **Solution:** Make sure only ONE user class is checked in the UI

**Problem:** Can't see user class selection
- **Solution:** Look for "User classes" section or user class picker in the main page

**Problem:** Want to test with specific short codes
- **Solution:** Set `LOCUST_SHORT_CODES` environment variable before starting Locust:
  ```bash
  LOCUST_SHORT_CODES=abc123,def456 docker compose restart locust-master locust-worker
  ```

## Test Endpoints

1. **POST /shorten** - Create short URL
   - Payload: `{"original_url": "https://example.com/path"}`
   - Expected: 200 OK with short_code

2. **GET /{short_code}** - Redirect to original URL
   - Expected: 301 Redirect (or 404 if not found)

3. **GET /stats/{short_code}** - Get analytics
   - Expected: 200 OK with stats (or 404 if no data)

## Performance Metrics

Locust will track:
- **Response Times** - Min, Max, Average, Median, 95th percentile
- **Requests per Second (RPS)** - Throughput
- **Failure Rate** - Percentage of failed requests
- **User Count** - Number of concurrent users

## Example Test Scenarios

### Light Load (Development)
```bash
locust -f locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 1m
```

### Medium Load (Staging)
```bash
locust -f locustfile.py --host=http://localhost:8000 -u 50 -r 5 -t 5m
```

### Heavy Load (Production-like)
```bash
locust -f locustfile.py --host=http://localhost:8000 -u 200 -r 20 -t 10m
```

### Stress Test (Find Limits)
```bash
locust -f locustfile.py --host=http://localhost:8000 -u 1000 -r 50 -t 15m
```

## Tips

1. **Start Small**: Begin with low user counts and gradually increase
2. **Monitor Services**: Watch Docker containers, database, Redis, and RabbitMQ
3. **Check Logs**: Monitor application logs for errors
4. **Database**: Ensure PostgreSQL can handle the load
5. **Redis**: Monitor cache hit rates
6. **RabbitMQ**: Check queue depth for analytics events

## Troubleshooting

### Connection Refused
- Ensure services are running: `docker compose ps`
- Check host URL is correct

### High Failure Rate
- Check service logs: `docker compose logs url-shortener`
- Verify database connections
- Check Redis availability
- Monitor resource usage (CPU, Memory)

### Slow Response Times
- Check database query performance
- Verify Redis cache is working
- Monitor connection pool usage
- Check for bottlenecks in the application


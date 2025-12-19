FROM python:3.14-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Install Locust
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy Locust test files
COPY locustfile.py .

# Expose Locust web UI port (master) and worker port
EXPOSE 8089 5557

# Default command (will be overridden in docker-compose)
# Master: locust --master --host=http://url-shortener-app:8000
# Worker: locust --worker --master-host=locust-master
CMD ["locust"]


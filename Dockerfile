FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
# This layer will be cached unless requirements.txt changes
COPY requirements.txt .

# Install Python dependencies with pip cache
# Using BuildKit cache mount to persist pip cache between builds
# This significantly speeds up rebuilds when requirements.txt hasn't changed
# Docker layer caching: if requirements.txt doesn't change, this entire layer is reused
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code (this layer will rebuild when code changes)
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


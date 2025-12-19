FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files for dependency resolution (for better Docker layer caching)
# This layer will be cached unless pyproject.toml changes
COPY pyproject.toml .

# Install Python dependencies with uv using pyproject.toml (much faster than pip)
# Using BuildKit cache mount to persist uv cache between builds
# This significantly speeds up rebuilds when pyproject.toml hasn't changed
# Docker layer caching: if pyproject.toml doesn't change, this entire layer is reused
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e .

# Copy application code (this layer will rebuild when code changes)
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.14-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY consumer.py .

# Run the consumer
CMD ["python", "consumer.py"]


FROM python:3.14-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]


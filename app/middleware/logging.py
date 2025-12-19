from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time

logger = logging.getLogger("uvicorn.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response


def add_logging_middleware(app):
    """Add logging middleware to the FastAPI application."""
    app.add_middleware(LoggingMiddleware)

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import endpoints
from app.middleware.logging import add_logging_middleware
from app.core.redis_client import get_redis_client, close_redis_client
from app.core.worker_id import WorkerIDManager
from app.core.id_generator import SnowflakeIDGenerator
from app.core.id_service import set_id_generator
from app.core.analytics import get_analytics_publisher, close_analytics_publisher

logger = logging.getLogger(__name__)

app = FastAPI(
    title="URL Shortener Service API",
    description="A scalable URL shortener service with analytics capabilities",
    version="1.0.0",
)

# Configure CORS to allow Swagger UI and other frontend clients from any origin
# This allows Swagger UI to work when accessed from anywhere (localhost, online editors, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - enables Swagger UI from any domain
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, PATCH, etc.)
    allow_headers=["*"],  # Allow all headers (Content-Type, Authorization, X-Requested-With, etc.)
    expose_headers=["*"],  # Expose all response headers to the client
    max_age=3600,  # Cache preflight requests for 1 hour
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        # Initialize Redis
        redis_client = await get_redis_client()
        logger.info("Redis client initialized")
        
        # Initialize worker ID manager and acquire worker ID
        worker_id_manager = WorkerIDManager(redis_client)
        worker_id = await worker_id_manager.acquire_worker_id()
        logger.info(f"Acquired worker ID: {worker_id}")
        
        # Initialize ID generator with worker ID
        id_generator = SnowflakeIDGenerator(worker_id)
        set_id_generator(id_generator)
        logger.info("ID generator initialized")
        
        # Store worker_id_manager in app state for shutdown
        app.state.worker_id_manager = worker_id_manager
        
        # Initialize RabbitMQ analytics (non-blocking, will log if fails)
        await get_analytics_publisher()
        
        logger.info("Application startup complete")
    
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on application shutdown."""
    try:
        # Release worker ID
        if hasattr(app.state, "worker_id_manager"):
            worker_id_manager = app.state.worker_id_manager
            await worker_id_manager.release_worker_id()
            logger.info("Worker ID released")
        
        # Close RabbitMQ connection
        await close_analytics_publisher()
        
        # Close Redis connection
        await close_redis_client()
        
        logger.info("Application shutdown complete")
    
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


app.include_router(endpoints.router)

add_logging_middleware(app)

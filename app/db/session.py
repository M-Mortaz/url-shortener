"""Database session management with connection pooling."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.setting import settings

# Create async database engine with connection pooling
# The engine manages a pool of database connections that are reused across requests
engine = create_async_engine(
    settings.PG_DSN,
    echo=settings.DB_ECHO,  # Log all SQL queries (useful for debugging, disable in production)
    pool_size=settings.DB_POOL_SIZE,  # Number of connections to keep open in the pool
    max_overflow=settings.DB_MAX_OVERFLOW,  # Maximum additional connections beyond pool_size that can be created on demand
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Seconds to wait before giving up on getting a connection from the pool
    pool_recycle=settings.DB_POOL_RECYCLE,  # Seconds after which a connection is recreated (prevents stale connections)
    pool_pre_ping=True,  # Verify connections are alive before using them (handles database restarts gracefully)
)


def create_async_session():
    """
    Create a session factory for async database sessions.
    
    Returns:
        A sessionmaker that creates AsyncSession instances bound to the engine.
    """
    return sessionmaker(
        bind=engine,  # Use the pooled engine for all sessions
        autocommit=False,  # Require explicit commit/rollback (safer)
        autoflush=False,  # Don't automatically flush changes (better performance)
        expire_on_commit=False,  # Keep objects accessible after commit (useful for returning data)
        class_=AsyncSession,  # Use async session class
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get a database session.
    
    Creates a new session from the pool, yields it for use in the request,
    and automatically closes it when done. Handles rollback on exceptions.
    
    Yields:
        AsyncSession: Database session from the connection pool
        
    Example:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            # Use session here
            result = await session.exec(select(Item))
            return result.all()
    """
    async_session = create_async_session()
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()  # Rollback transaction on error
            raise e
        finally:
            await session.close()  # Return connection to pool

"""Configuration definition."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "settings"]

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class EnvSettingsOptions(Enum):
    production = "production"
    staging = "staging"
    development = "dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # Project Configuration
    ENV_SETTING: EnvSettingsOptions = Field(
        "production", examples=["production", "staging", "dev"]
    )
    # Example "postgresql+psycopg://username:password@localhost:5432/db_name"
    PG_DSN: str = Field()
    
    # Redis Configuration
    # Example "redis://localhost:6379/0"
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # RabbitMQ Configuration
    # Example "amqp://guest:guest@localhost:5672/"
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    RABBITMQ_EXCHANGE: str = Field(default="url_shortener")
    RABBITMQ_QUEUE: str = Field(default="click_events")
    
    # Worker ID Configuration
    WORKER_ID_LEASE_TTL: int = Field(default=60, description="Worker ID lease TTL in seconds")
    WORKER_ID_RENEWAL_INTERVAL: int = Field(default=30, description="Worker ID renewal interval in seconds")
    MAX_WORKER_ID: int = Field(default=1023, description="Maximum worker ID (10 bits = 0-1023)")
    
    # Application Configuration
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL for short link generation")
    
    # Database Connection Pool Configuration
    # pool_size: Number of connections to keep open in the pool at all times
    #   - Higher values = more connections ready, but more database resources used
    #   - Lower values = fewer resources, but may need to create connections on demand
    DB_POOL_SIZE: int = Field(default=20, description="Number of connections to maintain in the pool")
    
    # max_overflow: Maximum additional connections beyond pool_size that can be created on demand
    #   - When pool is exhausted, can create up to max_overflow more connections
    #   - Total possible connections = pool_size + max_overflow
    #   - Set to 0 to disable overflow (strict pool_size limit)
    DB_MAX_OVERFLOW: int = Field(default=10, description="Maximum number of connections to allow beyond pool_size")
    
    # pool_timeout: Seconds to wait before giving up on getting a connection from the pool
    #   - If all connections are in use and max_overflow is reached, wait this long
    #   - After timeout, raises TimeoutError
    DB_POOL_TIMEOUT: int = Field(default=30, description="Seconds to wait before giving up on getting a connection")
    
    # pool_recycle: Seconds after which a connection is recreated
    #   - Prevents using stale connections that may have been closed by the database
    #   - Important for long-running applications
    #   - Set to -1 to disable (not recommended)
    DB_POOL_RECYCLE: int = Field(default=3600, description="Seconds after which a connection is recreated")
    
    # DB_ECHO: Enable SQL query logging to console
    #   - Useful for debugging and development
    #   - Should be False in production for performance and security
    DB_ECHO: bool = Field(default=False, description="Enable SQL query logging")


settings = Settings()

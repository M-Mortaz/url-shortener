"""Worker ID leasing system using Redis for safe autoscaling."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from redis.asyncio import Redis

from app.core.setting import settings

__all__ = ["WorkerIDManager"]

logger = logging.getLogger(__name__)


class WorkerIDManager:
    """
    Manages worker ID leasing from Redis.
    
    Uses atomic Redis operations to ensure no two processes share the same
    worker ID, preventing ID collisions in the Snowflake generator.
    """
    
    REDIS_KEY_PREFIX = "worker_id:lease:"
    
    def __init__(self, redis_client: Redis):
        """
        Initialize the worker ID manager.
        
        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
        self.worker_id: Optional[int] = None
        self.renewal_task: Optional[asyncio.Task] = None
        self.lease_ttl = settings.WORKER_ID_LEASE_TTL
        self.renewal_interval = settings.WORKER_ID_RENEWAL_INTERVAL
    
    async def acquire_worker_id(self) -> int:
        """
        Acquire a unique worker ID from Redis.
        
        Tries to lease an available worker ID (0 to MAX_WORKER_ID).
        Uses atomic SETNX operations to ensure only one process gets each ID.
        
        Returns:
            Acquired worker ID
            
        Raises:
            RuntimeError: If no worker ID is available
        """
        max_worker_id = settings.MAX_WORKER_ID
        
        for candidate_id in range(max_worker_id + 1):
            key = f"{self.REDIS_KEY_PREFIX}{candidate_id}"
            
            # Try to acquire the lease atomically
            # SETNX sets the key only if it doesn't exist
            acquired = await self.redis.set(
                key,
                "leased",
                nx=True,  # Only set if not exists
                ex=self.lease_ttl  # Set expiration
            )
            
            if acquired:
                self.worker_id = candidate_id
                logger.info(f"Acquired worker ID: {candidate_id}")
                
                # Start renewal task
                self.renewal_task = asyncio.create_task(self._renew_lease_loop())
                
                return candidate_id
        
        raise RuntimeError(
            f"No available worker IDs (0-{max_worker_id}). "
            "All worker IDs are currently leased."
        )
    
    async def release_worker_id(self) -> None:
        """
        Release the leased worker ID.
        
        Cancels the renewal task and deletes the Redis key.
        """
        if self.renewal_task:
            self.renewal_task.cancel()
            try:
                await self.renewal_task
            except asyncio.CancelledError:
                pass
            self.renewal_task = None
        
        if self.worker_id is not None:
            key = f"{self.REDIS_KEY_PREFIX}{self.worker_id}"
            await self.redis.delete(key)
            logger.info(f"Released worker ID: {self.worker_id}")
            self.worker_id = None
    
    async def _renew_lease_loop(self) -> None:
        """
        Background task to periodically renew the worker ID lease.
        
        Renews the lease every renewal_interval seconds to prevent
        expiration if the process is still alive.
        """
        if self.worker_id is None:
            return
        
        key = f"{self.REDIS_KEY_PREFIX}{self.worker_id}"
        
        try:
            while True:
                await asyncio.sleep(self.renewal_interval)
                
                # Renew the lease by extending TTL
                renewed = await self.redis.expire(key, self.lease_ttl)
                
                if not renewed:
                    # Key doesn't exist anymore, try to reacquire
                    logger.warning(
                        f"Worker ID {self.worker_id} lease expired. "
                        "Attempting to reacquire..."
                    )
                    await self.redis.set(key, "leased", nx=True, ex=self.lease_ttl)
                
                logger.debug(f"Renewed lease for worker ID: {self.worker_id}")
        
        except asyncio.CancelledError:
            logger.debug("Lease renewal task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in lease renewal loop: {e}", exc_info=True)
    
    @property
    def current_worker_id(self) -> Optional[int]:
        """Get the currently leased worker ID."""
        return self.worker_id


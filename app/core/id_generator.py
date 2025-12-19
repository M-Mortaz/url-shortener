"""Snowflake-style ID generator with Base62 encoding."""

from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = ["SnowflakeIDGenerator", "base62_encode", "base62_decode"]

# Base62 character set: 0-9, a-z, A-Z
BASE62_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(num: int) -> str:
    """
    Encode a positive integer to Base62 string.
    
    Args:
        num: Positive integer to encode
        
    Returns:
        Base62 encoded string
    """
    if num == 0:
        return BASE62_CHARS[0]
    
    encoded = []
    while num > 0:
        encoded.append(BASE62_CHARS[num % 62])
        num //= 62
    
    return "".join(reversed(encoded))


def base62_decode(encoded: str) -> int:
    """
    Decode a Base62 string to integer.
    
    Args:
        encoded: Base62 encoded string
        
    Returns:
        Decoded integer
    """
    num = 0
    for char in encoded:
        num = num * 62 + BASE62_CHARS.index(char)
    return num


class SnowflakeIDGenerator:
    """
    Snowflake-style ID generator.
    
    ID structure (64 bits):
    - 41 bits: Timestamp (milliseconds since custom epoch)
    - 10 bits: Worker ID (0-1023)
    - 12 bits: Sequence (0-4095 per millisecond)
    
    Custom epoch: 2024-01-01 00:00:00 UTC (1704067200000 ms)
    """
    
    # Bit allocations
    TIMESTAMP_BITS = 41
    WORKER_ID_BITS = 10
    SEQUENCE_BITS = 12
    
    # Maximum values
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1  # 1023
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095
    
    # Custom epoch: 2024-01-01 00:00:00 UTC
    EPOCH = 1704067200000  # milliseconds
    
    def __init__(self, worker_id: int):
        """
        Initialize the ID generator.
        
        Args:
            worker_id: Unique worker ID (0-1023)
            
        Raises:
            ValueError: If worker_id is out of range
        """
        if not 0 <= worker_id <= self.MAX_WORKER_ID:
            raise ValueError(f"Worker ID must be between 0 and {self.MAX_WORKER_ID}")
        
        self.worker_id = worker_id
        self.sequence = 0
        self.last_timestamp = -1
    
    def generate(self) -> int:
        """
        Generate a new Snowflake ID.
        
        Returns:
            64-bit Snowflake ID
            
        Raises:
            RuntimeError: If clock moves backwards or sequence overflows
        """
        timestamp = self._current_timestamp()
        
        if timestamp < self.last_timestamp:
            raise RuntimeError(
                f"Clock moved backwards. Refusing to generate ID for "
                f"{self.last_timestamp - timestamp} milliseconds"
            )
        
        if timestamp == self.last_timestamp:
            # Same millisecond, increment sequence
            self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
            if self.sequence == 0:
                # Sequence overflow, wait for next millisecond
                logger.warning(
                    f"Sequence overflow detected for worker {self.worker_id}. "
                    f"Generated {self.MAX_SEQUENCE + 1} IDs in the same millisecond. "
                    "Waiting for next millisecond to continue."
                )
                timestamp = self._wait_next_millisecond(self.last_timestamp)
        else:
            # New millisecond, reset sequence
            self.sequence = 0
        
        self.last_timestamp = timestamp
        
        # Build the ID
        id_value = (
            ((timestamp - self.EPOCH) << (self.WORKER_ID_BITS + self.SEQUENCE_BITS))
            | (self.worker_id << self.SEQUENCE_BITS)
            | self.sequence
        )
        
        return id_value
    
    def generate_short_code(self) -> str:
        """
        Generate a new Snowflake ID and encode it to Base62.
        
        Returns:
            Base62 encoded short code
        """
        return base62_encode(self.generate())
    
    def _current_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
    
    def _wait_next_millisecond(self, last_timestamp: int) -> int:
        """Wait until next millisecond."""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp
    
    @classmethod
    def parse_id(cls, id_value: int) -> dict[str, int]:
        """
        Parse a Snowflake ID into its components.
        
        Args:
            id_value: Snowflake ID to parse
            
        Returns:
            Dictionary with timestamp, worker_id, and sequence
        """
        sequence = id_value & cls.MAX_SEQUENCE
        worker_id = (id_value >> cls.SEQUENCE_BITS) & cls.MAX_WORKER_ID
        timestamp = (id_value >> (cls.WORKER_ID_BITS + cls.SEQUENCE_BITS)) + cls.EPOCH
        
        return {
            "timestamp": timestamp,
            "worker_id": worker_id,
            "sequence": sequence,
        }


"""ID generator service singleton."""

from __future__ import annotations

from typing import Optional

from app.core.id_generator import SnowflakeIDGenerator

__all__ = ["get_id_generator", "id_generator"]

# Global ID generator instance
id_generator: Optional[SnowflakeIDGenerator] = None


def get_id_generator() -> SnowflakeIDGenerator:
    """
    Get the global ID generator instance.
    
    Returns:
        SnowflakeIDGenerator instance
        
    Raises:
        RuntimeError: If ID generator is not initialized
    """
    if id_generator is None:
        raise RuntimeError("ID generator not initialized. Call set_id_generator() first.")
    return id_generator


def set_id_generator(generator: SnowflakeIDGenerator) -> None:
    """
    Set the global ID generator instance.
    
    Args:
        generator: ID generator instance
    """
    global id_generator
    id_generator = generator


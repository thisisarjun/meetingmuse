"""Storage adapters for different backends."""

from .memory_storage import MemoryStorageAdapter
from .storage_adapter import StorageAdapter

__all__ = ["StorageAdapter", "MemoryStorageAdapter"]

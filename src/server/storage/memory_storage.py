"""In-memory storage adapter implementation."""

from typing import Any, Dict, Optional

from .storage_adapter import StorageAdapter


class MemoryStorageAdapter(StorageAdapter):
    """In-memory storage adapter."""

    def __init__(self) -> None:
        self._storage: Dict[str, Any] = {}

    async def get(self, key: str) -> Optional[str]:
        return str(self._storage.get(key))

    async def set(self, key: str, value: str) -> bool:
        try:
            self._storage[key] = value
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        if key in self._storage:
            del self._storage[key]
            return True
        return False

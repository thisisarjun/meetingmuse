"""Storage adapter interface for different storage backends."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class StorageAdapter(ABC):
    """Abstract storage adapter interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key.

        Args:
            key: Storage key

        Returns:
            Value if found, None otherwise
        """

    @abstractmethod
    async def set(self, key: str, value: Any) -> bool:
        """Set value by key.

        Args:
            key: Storage key
            value: Value to store

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    async def get_all_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get all key-value pairs with given prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Dictionary of matching key-value pairs
        """

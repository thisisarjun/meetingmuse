from typing import Optional, cast

from redis.asyncio import Redis

from server.storage.storage_adapter import StorageAdapter


class RedisStorageAdapter(StorageAdapter):
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    # TODO: make base class always return a string
    async def get(self, key: str) -> Optional[str]:
        return cast(Optional[str], await self.redis_client.get(key))

    async def set(self, key: str, value: str) -> bool:
        return bool(await self.redis_client.set(key, value))

    async def delete(self, key: str) -> bool:
        return bool(await self.redis_client.delete(key))

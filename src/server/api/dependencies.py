from redis.asyncio import Redis

from common.config import config
from common.logger.logger import Logger
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager
from server.storage.memory_storage import MemoryStorageAdapter
from server.storage.redis_adapter import RedisStorageAdapter
from server.storage.storage_adapter import StorageAdapter

# Global service instances
_storage_adapter: StorageAdapter | None = None
_session_manager: SessionManager | None = None
_oauth_service: OAuthService | None = None


def get_logger() -> Logger:
    """Dependency to get logger instance"""
    return Logger()


def get_storage_adapter(type: str = "memory") -> StorageAdapter:
    """Dependency to get storage adapter instance"""
    global _storage_adapter
    if type == "redis":
        redis_client = Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True,
        )
        _storage_adapter = RedisStorageAdapter(redis_client)
    elif type == "memory":
        _storage_adapter = MemoryStorageAdapter()
    else:
        raise ValueError(f"Invalid storage adapter type: {type}")
    return _storage_adapter


def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(get_storage_adapter("redis"))
    return _session_manager


def get_oauth_service() -> OAuthService:
    """Dependency to get OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService(get_session_manager(), get_logger())
    return _oauth_service

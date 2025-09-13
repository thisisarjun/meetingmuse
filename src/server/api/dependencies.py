from common.logger.logger import Logger
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager
from server.storage.memory_storage import MemoryStorageAdapter
from server.storage.storage_adapter import StorageAdapter

# Global service instances
_storage_adapter: StorageAdapter | None = None
_session_manager: SessionManager | None = None
_oauth_service: OAuthService | None = None


def get_logger() -> Logger:
    """Dependency to get logger instance"""
    return Logger()


def get_storage_adapter() -> StorageAdapter:
    """Dependency to get storage adapter instance"""
    global _storage_adapter
    if _storage_adapter is None:
        # Swap adapter with appropriate storage in production
        _storage_adapter = MemoryStorageAdapter()
    return _storage_adapter


def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(get_storage_adapter())
    return _session_manager


def get_oauth_service() -> OAuthService:
    """Dependency to get OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService(get_session_manager(), get_logger())
    return _oauth_service

from common.config.config import config
from common.logger.logger import Logger
from server.dependency_container import DependencyContainer
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager
from server.storage.storage_adapter import StorageAdapter

# Global dependency container instance - initialized based on environment
_container: DependencyContainer | None = None


def get_container() -> DependencyContainer:
    """Get the global dependency container instance"""
    global _container
    if _container is None:
        if config.ENV == "dev":
            _container = DependencyContainer.create_development()
        else:
            _container = DependencyContainer.create_production()
    return _container


def get_logger() -> Logger:
    """Dependency to get logger instance"""
    return get_container().logger


def get_storage_adapter() -> StorageAdapter:
    """Dependency to get storage adapter instance"""
    return get_container().storage_adapter


def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance"""
    return get_container().session_manager


def get_oauth_service() -> OAuthService:
    """Dependency to get OAuth service instance"""
    return get_container().oauth_service

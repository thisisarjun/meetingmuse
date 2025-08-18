from common.logger.logger import Logger
from server.services.oauth_service import OAuthService
from server.services.token_storage import InMemoryTokenStorage

_token_storage: InMemoryTokenStorage | None = None
_oauth_service: OAuthService | None = None


def get_logger() -> Logger:
    """Dependency to get logger instance"""
    return Logger()


def get_token_storage() -> InMemoryTokenStorage:
    """Dependency to get token storage instance"""
    global _token_storage
    if _token_storage is None:
        _token_storage = InMemoryTokenStorage()
    return _token_storage


def get_oauth_service() -> OAuthService:
    """Dependency to get OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService(get_token_storage())
    return _oauth_service

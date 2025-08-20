"""Tests for authentication API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from common.logger.logger import Logger
from server.api.auth_api import (
    get_auth_status,
    logout,
    oauth_callback,
    refresh_access_token,
    start_oauth_flow,
)
from server.models.api.auth import (
    AuthUrlResponse,
    LogoutResponse,
    RefreshResponse,
    StatusResponse,
)
from server.models.session import TokenInfo, UserSession
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager


class TestAuthAPI:
    """Test suite for authentication API endpoints."""

    @pytest.fixture
    def mock_oauth_service(self):
        """Mock OAuth service."""
        service = Mock(spec=OAuthService)
        service.get_authorization_url = AsyncMock()
        service.handle_callback = AsyncMock()
        service.refresh_token = AsyncMock()
        service.revoke_token = AsyncMock()
        service.validate_token = AsyncMock()
        return service

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager."""
        manager = Mock(spec=SessionManager)
        manager.get_session_by_client_id = AsyncMock()
        return manager

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        return Mock(spec=Logger)

    @pytest.fixture
    def sample_session(self):
        """Sample user session."""
        return UserSession(
            session_id="test_session_123",
            client_id="test_client_123",
            tokens=TokenInfo(
                access_token="test_access_token",
                refresh_token="test_refresh_token",
                token_expiry=datetime(2024, 12, 31, tzinfo=timezone.utc),
                scopes=["calendar.read", "calendar.write"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_start_oauth_flow_success(self, mock_oauth_service, mock_logger):
        """Test successful OAuth flow start."""
        # Arrange
        client_id = "test_client_123"
        mock_oauth_service.get_authorization_url.return_value = (
            "https://oauth.example.com/auth?client_id=123",
            "test_state_456",
        )

        # Act
        result = await start_oauth_flow(client_id, mock_oauth_service, mock_logger)

        # Assert
        assert isinstance(result, AuthUrlResponse)
        assert result.client_id == client_id
        assert (
            result.authorization_url == "https://oauth.example.com/auth?client_id=123"
        )
        assert result.state == "test_state_456"
        mock_oauth_service.get_authorization_url.assert_called_once_with(client_id)

    @pytest.mark.asyncio
    async def test_start_oauth_flow_invalid_client_id(
        self, mock_oauth_service, mock_logger
    ):
        """Test OAuth flow start with invalid client_id."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await start_oauth_flow("", mock_oauth_service, mock_logger)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid client_id"

    @pytest.mark.asyncio
    async def test_oauth_callback_success(
        self, mock_oauth_service, mock_logger, sample_session
    ):
        """Test successful OAuth callback."""
        # Arrange
        code = "auth_code_123"
        state = "test_state_456"
        mock_oauth_service.handle_callback.return_value = sample_session

        # Act
        result = await oauth_callback(
            code, state, None, mock_oauth_service, mock_logger
        )

        # Assert
        assert isinstance(result, RedirectResponse)
        assert "auth_success=true" in result.headers["location"]
        mock_oauth_service.handle_callback.assert_called_once_with(code, state)

    @pytest.mark.asyncio
    async def test_oauth_callback_with_error(self, mock_oauth_service, mock_logger):
        """Test OAuth callback with error parameter."""
        # Act
        result = await oauth_callback(
            None, None, "access_denied", mock_oauth_service, mock_logger
        )

        # Assert
        assert isinstance(result, RedirectResponse)
        assert "auth_error=access_denied" in result.headers["location"]

    @pytest.mark.asyncio
    async def test_oauth_callback_missing_parameters(
        self, mock_oauth_service, mock_logger
    ):
        """Test OAuth callback with missing code/state."""
        # Act
        result = await oauth_callback(None, None, None, mock_oauth_service, mock_logger)

        # Assert
        assert isinstance(result, RedirectResponse)
        assert "auth_error=missing_parameters" in result.headers["location"]

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, mock_oauth_service, mock_logger):
        """Test successful token refresh."""
        # Arrange
        session_id = "test_session_123"
        token_info = TokenInfo(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_expiry=datetime(2024, 12, 31, tzinfo=timezone.utc),
            scopes=["calendar.read"],
        )
        mock_oauth_service.refresh_token.return_value = token_info

        # Act
        result = await refresh_access_token(session_id, mock_oauth_service, mock_logger)

        # Assert
        assert isinstance(result, RefreshResponse)
        assert result.message == "Token refreshed successfully"
        assert result.expires_at == "2024-12-31T00:00:00+00:00"
        mock_oauth_service.refresh_token.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_refresh_access_token_failed(self, mock_oauth_service, mock_logger):
        """Test failed token refresh."""
        # Arrange
        session_id = "invalid_session"
        mock_oauth_service.refresh_token.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(session_id, mock_oauth_service, mock_logger)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Session not found or refresh failed"

    @pytest.mark.asyncio
    async def test_logout_success(
        self, mock_session_manager, mock_oauth_service, mock_logger, sample_session
    ):
        """Test successful logout."""
        # Arrange
        client_id = "test_client_123"
        mock_session_manager.get_session_by_client_id.return_value = sample_session
        mock_oauth_service.revoke_token.return_value = True

        # Act
        result = await logout(
            client_id, mock_session_manager, mock_oauth_service, mock_logger
        )

        # Assert
        assert isinstance(result, LogoutResponse)
        assert result.message == "Logout successful"
        mock_session_manager.get_session_by_client_id.assert_called_once_with(client_id)
        mock_oauth_service.revoke_token.assert_called_once_with(
            sample_session.session_id
        )

    @pytest.mark.asyncio
    async def test_logout_session_not_found(
        self, mock_session_manager, mock_oauth_service, mock_logger
    ):
        """Test logout with session not found."""
        # Arrange
        client_id = "nonexistent_client"
        mock_session_manager.get_session_by_client_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await logout(
                client_id, mock_session_manager, mock_oauth_service, mock_logger
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Session not found"

    @pytest.mark.asyncio
    async def test_get_auth_status_authenticated(
        self, mock_session_manager, mock_oauth_service, mock_logger, sample_session
    ):
        """Test auth status for authenticated client."""
        # Arrange
        client_id = "test_client_123"
        mock_session_manager.get_session_by_client_id.return_value = sample_session
        mock_oauth_service.validate_token.return_value = True

        # Act
        result = await get_auth_status(
            client_id, mock_session_manager, mock_oauth_service, mock_logger
        )

        # Assert
        assert isinstance(result, StatusResponse)
        assert result.authenticated is True
        assert result.client_id == client_id
        assert result.session_id == sample_session.session_id
        assert result.scopes == sample_session.tokens.scopes
        assert result.message == "Authenticated"

    @pytest.mark.asyncio
    async def test_get_auth_status_not_authenticated(
        self, mock_session_manager, mock_oauth_service, mock_logger
    ):
        """Test auth status for non-authenticated client."""
        # Arrange
        client_id = "test_client_123"
        mock_session_manager.get_session_by_client_id.return_value = None

        # Act
        result = await get_auth_status(
            client_id, mock_session_manager, mock_oauth_service, mock_logger
        )

        # Assert
        assert isinstance(result, StatusResponse)
        assert result.authenticated is False
        assert result.client_id == client_id
        assert result.message == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_auth_status_invalid_client_id(
        self, mock_session_manager, mock_oauth_service, mock_logger
    ):
        """Test auth status with invalid client_id."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_status(
                "", mock_session_manager, mock_oauth_service, mock_logger
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid client_id"

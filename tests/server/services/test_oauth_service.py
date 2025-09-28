"""
Test suite for OAuthService.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.models.session import TokenInfo, UserSession


class TestOAuthService:
    """Test suite for OAuthService."""

    async def test_get_authorization_url(self, oauth_service):
        """Test getting authorization URL."""
        client_id = "test_client_123"

        authorization_url, state = await oauth_service.get_authorization_url(client_id)

        assert isinstance(authorization_url, str)
        assert "accounts.google.com" in authorization_url
        assert "oauth2/auth" in authorization_url
        assert isinstance(state, str)
        assert len(state) > 0

    async def test_handle_callback_success(self, oauth_service, mock_session_manager):
        """Test successful OAuth callback handling."""
        code = "test_auth_code"
        state = "test_client_123:test_state"

        mock_credentials = Mock()
        mock_credentials.token = "access_token"
        mock_credentials.refresh_token = "refresh_token"
        mock_credentials.expiry = datetime.now(timezone.utc)
        mock_credentials.scopes = ["scope1", "scope2"]

        with patch("server.services.oauth_service.Flow") as mock_flow_class:
            mock_flow = Mock()
            mock_flow.credentials = mock_credentials
            mock_flow_class.from_client_config.return_value = mock_flow

            result = await oauth_service.handle_callback(code, state)

            assert isinstance(result, UserSession)
            assert result.client_id == "test_client_123"
            assert result.tokens.access_token == "access_token"
            mock_session_manager.store_session.assert_called_once()

    async def test_handle_callback_invalid_state(self, oauth_service):
        """Test OAuth callback with invalid state."""
        code = "test_auth_code"
        state = "invalid_state_format"

        with pytest.raises(ValueError, match="Invalid state parameter"):
            await oauth_service.handle_callback(code, state)

    async def test_validate_token_valid(self, oauth_service, mock_session_manager):
        """Test token validation with valid token."""
        session_id = "test_session_123"
        future_expiry = datetime.now(timezone.utc).replace(year=2030)

        mock_session = UserSession(
            session_id=session_id,
            client_id="test_client",
            tokens=TokenInfo(
                access_token="valid_token",
                refresh_token="refresh_token",
                token_expiry=future_expiry,
                scopes=["scope1"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_session_manager.get_session.return_value = mock_session

        result = await oauth_service.validate_token(session_id)

        assert result is True

    async def test_validate_token_expired(self, oauth_service, mock_session_manager):
        """Test token validation with expired token."""
        session_id = "test_session_123"
        past_expiry = datetime.now(timezone.utc).replace(year=2020)

        mock_session = UserSession(
            session_id=session_id,
            client_id="test_client",
            tokens=TokenInfo(
                access_token="expired_token",
                refresh_token="refresh_token",
                token_expiry=past_expiry,
                scopes=["scope1"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_session_manager.get_session.return_value = mock_session

        with patch.object(
            oauth_service, "refresh_token", return_value=None
        ) as mock_refresh:
            result = await oauth_service.validate_token(session_id)

        assert result is False
        mock_refresh.assert_called_once_with(session_id)

    async def test_validate_token_no_session(self, oauth_service, mock_session_manager):
        """Test token validation with no session."""
        session_id = "nonexistent_session"
        mock_session_manager.get_session.return_value = None

        result = await oauth_service.validate_token(session_id)

        assert result is False

    async def test_revoke_token_success(self, oauth_service, mock_session_manager):
        """Test successful token revocation."""
        session_id = "test_session_123"

        mock_session = UserSession(
            session_id=session_id,
            client_id="test_client",
            tokens=TokenInfo(
                access_token="token_to_revoke",
                refresh_token="refresh_token",
                token_expiry=None,
                scopes=["scope1"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.delete_session.return_value = True

        with patch("server.services.oauth_service.http_client") as mock_http:
            mock_http.post = AsyncMock()
            result = await oauth_service.revoke_token(session_id)

        assert result is True
        mock_session_manager.delete_session.assert_called_once_with(
            session_id, "test_client"
        )

    async def test_revoke_token_no_session(self, oauth_service, mock_session_manager):
        """Test token revocation with no session."""
        session_id = "nonexistent_session"
        mock_session_manager.get_session.return_value = None

        result = await oauth_service.revoke_token(session_id)

        assert result is False

    async def test_get_credentials_valid(self, oauth_service, mock_session_manager):
        """Test getting valid credentials."""
        session_id = "test_session_123"

        mock_session = UserSession(
            session_id=session_id,
            client_id="test_client",
            tokens=TokenInfo(
                access_token="valid_token",
                refresh_token="refresh_token",
                token_expiry=None,
                scopes=["scope1"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_session_manager.get_session.return_value = mock_session

        with patch.object(oauth_service, "validate_token", return_value=True):
            result = await oauth_service.get_credentials(session_id)

        assert result is not None
        assert result.token == "valid_token"

    async def test_get_credentials_invalid_token(
        self, oauth_service, mock_session_manager
    ):
        """Test getting credentials with invalid token."""
        session_id = "test_session_123"

        mock_session = UserSession(
            session_id=session_id,
            client_id="test_client",
            tokens=TokenInfo(
                access_token="invalid_token",
                refresh_token="refresh_token",
                token_expiry=None,
                scopes=["scope1"],
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_session_manager.get_session.return_value = mock_session

        with patch.object(oauth_service, "validate_token", return_value=False):
            result = await oauth_service.get_credentials(session_id)

        assert result is None

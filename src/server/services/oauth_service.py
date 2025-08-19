"""Google OAuth 2.0 authentication service."""

import secrets
from datetime import datetime, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from common.config.config import config
from common.http_client import http_client
from server.models.oauth import ClientConfig, WebClientConfig
from server.models.session import TokenInfo, UserSession
from server.services.session_manager import SessionManager


class OAuthService:
    """Handles Google OAuth 2.0 authentication flow."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialize OAuth service with Google configuration.

        Args:
            session_manager: Session manager for handling OAuth sessions
        """
        self._session_manager = session_manager
        self._client_config = ClientConfig(
            web=WebClientConfig(
                client_id=config.GOOGLE_CLIENT_ID,
                client_secret=config.GOOGLE_CLIENT_SECRET,
                redirect_uris=[config.GOOGLE_REDIRECT_URI],
                auth_uri="https://accounts.google.com/o/oauth2/auth",
                token_uri="https://oauth2.googleapis.com/token",
            )
        )

    def _create_flow(self, state: Optional[str] = None) -> Flow:
        """Create OAuth flow."""
        flow = Flow.from_client_config(
            client_config=self._client_config.model_dump(),
            scopes=config.GOOGLE_SCOPES,
        )
        flow.redirect_uri = config.GOOGLE_REDIRECT_URI
        if state:
            flow.state = state
        return flow

    async def get_authorization_url(self, client_id: str) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            client_id: Unique client identifier

        Returns:
            Tuple of (authorization_url, state)
        """
        flow = self._create_flow()

        # Generate state parameter for security
        state = secrets.token_urlsafe(32)

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=f"{client_id}:{state}",  # Include client_id in state
        )

        return authorization_url, state

    async def handle_callback(self, code: str, state: str) -> UserSession:
        """
        Process OAuth callback and exchange code for tokens.

        Args:
            code: Authorization code from Google
            state: State parameter for security validation

        Returns:
            UserSession with token information

        Raises:
            ValueError: If state is invalid or callback fails
        """
        try:
            client_id, _ = state.split(":", 1)
        except ValueError:
            raise ValueError("Invalid state parameter")

        if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
            raise ValueError(
                "Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )

        flow = self._create_flow()

        try:
            # Exchange code for tokens
            flow.fetch_token(code=code)

            credentials = flow.credentials

            expiry = credentials.expiry
            if expiry and expiry.tzinfo is None:
                # Convert to UTC
                expiry = expiry.replace(tzinfo=timezone.utc)

            token_info = TokenInfo(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=expiry,
                scopes=list(credentials.scopes or []),
            )

            # Create session
            session_id = secrets.token_urlsafe(32)
            session = UserSession(
                session_id=session_id,
                client_id=client_id,
                tokens=token_info,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Store session
            await self._session_manager.store_session(session)

            return session

        except Exception as e:
            raise ValueError(f"OAuth callback failed: {str(e)}")

    async def refresh_token(self, session_id: str) -> Optional[TokenInfo]:
        """
        Refresh access token using refresh token.

        Args:
            session_id: Session identifier

        Returns:
            Updated TokenInfo or None if refresh failed
        """
        session = await self._session_manager.get_session(session_id)
        if not session or not session.tokens.refresh_token:
            return None

        try:
            credentials = Credentials(
                token=session.tokens.access_token,
                refresh_token=session.tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=config.GOOGLE_CLIENT_ID,
                client_secret=config.GOOGLE_CLIENT_SECRET,
                scopes=session.tokens.scopes,
            )

            # Refresh the credentials
            credentials.refresh(Request())

            expiry = credentials.expiry
            if expiry and expiry.tzinfo is None:
                # Convert to UTC
                expiry = expiry.replace(tzinfo=timezone.utc)

            new_token_info = TokenInfo(
                access_token=str(credentials.token),
                refresh_token=credentials.refresh_token or session.tokens.refresh_token,
                token_expiry=expiry,
                scopes=list(credentials.scopes or session.tokens.scopes),
            )

            # Update session
            await self._session_manager.update_session_tokens(
                session_id, new_token_info
            )

            return new_token_info

        except Exception:
            return None

    async def validate_token(self, session_id: str) -> bool:
        """
        Validate access token.

        Args:
            session_id: Session identifier

        Returns:
            True if token is valid, False otherwise
        """
        session = await self._session_manager.get_session(session_id)
        if not session:
            return False

        # Check if token is expired
        if session.tokens.token_expiry and session.tokens.token_expiry <= datetime.now(
            timezone.utc
        ):
            # Try to refresh
            refreshed = await self.refresh_token(session_id)
            return refreshed is not None

        return True

    async def revoke_token(self, session_id: str) -> bool:
        """
        Revoke access token and remove session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        session = await self._session_manager.get_session(session_id)
        if not session:
            return False

        try:
            await http_client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": session.tokens.access_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        except Exception:
            pass  # Continue even if revocation fails

        # Remove session
        return await self._session_manager.delete_session(session_id)

    # TODO: Use this method to make Calendar API calls
    async def get_credentials(self, session_id: str) -> Optional[Credentials]:
        """
        Get Google credentials for API calls.

        Args:
            session_id: Session identifier

        Returns:
            Google credentials or None if invalid
        """
        session = await self._session_manager.get_session(session_id)
        if not session:
            return None

        # Check if we need to refresh
        if not await self.validate_token(session_id):
            return None

        # Get updated session after potential refresh
        session = await self._session_manager.get_session(session_id)
        if not session:
            return None

        return Credentials(
            token=session.tokens.access_token,
            refresh_token=session.tokens.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            scopes=session.tokens.scopes,
        )

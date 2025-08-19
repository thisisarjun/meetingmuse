"""Session manager for handling OAuth sessions with encryption."""

import base64
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet

from common.config.config import config
from server.models.session import TokenInfo, UserSession
from server.storage.storage_adapter import StorageAdapter


class SessionManager:
    """Manages OAuth sessions with encrypted token storage."""

    def __init__(self, storage_adapter: StorageAdapter) -> None:
        """Initialize session manager.

        Args:
            storage_adapter: Storage adapter for persisting sessions
        """
        self._storage = storage_adapter
        self._encryption_key = self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key)

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        key_str = config.SESSION_ENCRYPTION_KEY.ljust(32)[:32]
        return base64.urlsafe_b64encode(key_str.encode())

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token."""
        encrypted_bytes: bytes = self._cipher.encrypt(token.encode())
        return encrypted_bytes.decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token."""
        decrypted_bytes: bytes = self._cipher.decrypt(encrypted_token.encode())
        return decrypted_bytes.decode()

    def _encrypt_session(self, session: UserSession) -> UserSession:
        """Encrypt session tokens."""
        return UserSession(
            session_id=session.session_id,
            client_id=session.client_id,
            tokens=TokenInfo(
                access_token=self._encrypt_token(session.tokens.access_token),
                refresh_token=self._encrypt_token(session.tokens.refresh_token)
                if session.tokens.refresh_token
                else None,
                token_expiry=session.tokens.token_expiry,
                scopes=session.tokens.scopes,
            ),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _decrypt_session(self, encrypted_session: UserSession) -> UserSession:
        """Decrypt session tokens."""
        return UserSession(
            session_id=encrypted_session.session_id,
            client_id=encrypted_session.client_id,
            tokens=TokenInfo(
                access_token=self._decrypt_token(encrypted_session.tokens.access_token),
                refresh_token=self._decrypt_token(
                    encrypted_session.tokens.refresh_token
                )
                if encrypted_session.tokens.refresh_token
                else None,
                token_expiry=encrypted_session.tokens.token_expiry,
                scopes=encrypted_session.tokens.scopes,
            ),
            created_at=encrypted_session.created_at,
            updated_at=encrypted_session.updated_at,
        )

    def _is_session_expired(self, session: UserSession) -> bool:
        """Check if session is expired."""
        if not session.tokens.token_expiry:
            return False
        return session.tokens.token_expiry <= datetime.now(timezone.utc)

    async def store_session(self, session: UserSession) -> bool:
        """Store a user session with encrypted tokens.

        Args:
            session: User session to store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            encrypted_session = self._encrypt_session(session)
            return await self._storage.set(session.session_id, encrypted_session)
        except Exception:
            return False

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve and decrypt a user session.

        Args:
            session_id: Session identifier

        Returns:
            Decrypted session if found and valid, None otherwise
        """
        try:
            encrypted_session = await self._storage.get(session_id)
            if not encrypted_session:
                return None

            # Check if session is expired
            if self._is_session_expired(encrypted_session):
                await self._storage.delete(session_id)
                return None

            return self._decrypt_session(encrypted_session)
        except Exception:
            return None

    async def update_session_tokens(self, session_id: str, tokens: TokenInfo) -> bool:
        """Update tokens for an existing session.

        Args:
            session_id: Session identifier
            tokens: New token information

        Returns:
            True if updated successfully, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        updated_session = UserSession(
            session_id=session.session_id,
            client_id=session.client_id,
            tokens=tokens,
            created_at=session.created_at,
            updated_at=datetime.now(),
        )

        return await self.store_session(updated_session)

    async def get_session_by_client_id(self, client_id: str) -> Optional[UserSession]:
        """Find session by client ID.

        Args:
            client_id: Client identifier

        Returns:
            Session if found, None otherwise
        """
        try:
            # Get all sessions and check client IDs
            all_sessions = await self._storage.get_all_by_prefix("")

            for session_id, encrypted_session in all_sessions.items():
                if encrypted_session.client_id == client_id:
                    return await self.get_session(session_id)

            return None
        except Exception:
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False otherwise
        """
        return await self._storage.delete(session_id)

    async def is_token_valid(self, session_id: str) -> bool:
        """Check if session tokens are valid.

        Args:
            session_id: Session identifier

        Returns:
            True if valid, False otherwise
        """
        session = await self.get_session(session_id)
        return session is not None

"""In-memory token storage service for OAuth sessions."""

import base64
from datetime import datetime, timezone
from typing import Dict, Optional

from cryptography.fernet import Fernet

from common.config.config import config
from server.models.session import TokenInfo, UserSession


class InMemoryTokenStorage:
    """In-memory token storage with encryption and automatic cleanup."""

    def __init__(self) -> None:
        """Initialize the token storage with encryption."""
        # Use configured encryption key or generate one for dev
        self._encryption_key = self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        self._sessions: Dict[str, UserSession] = {}

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        key_str = config.SESSION_ENCRYPTION_KEY.ljust(32)[:32]
        return base64.urlsafe_b64encode(key_str.encode())

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token."""
        encrypted_bytes: bytes = self._cipher.encrypt(token.encode())
        return str(encrypted_bytes.decode())

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token."""
        decrypted_bytes: bytes = self._cipher.decrypt(encrypted_token.encode())
        return str(decrypted_bytes.decode())

    async def store_session(self, session: UserSession) -> None:
        """Store a user session with encrypted tokens."""
        encrypted_session = UserSession(
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
            updated_at=datetime.now(),
        )
        self._sessions[session.session_id] = encrypted_session

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve a user session with decrypted tokens."""
        encrypted_session = self._sessions.get(session_id)
        if not encrypted_session:
            return None

        # Check if session is expired
        if (
            encrypted_session.tokens.token_expiry
            and encrypted_session.tokens.token_expiry <= datetime.now(timezone.utc)
        ):
            await self.delete_session(session_id)
            return None

        # Decrypt tokens
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

    async def update_tokens(self, session_id: str, tokens: TokenInfo) -> bool:
        """Update tokens for a session."""
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
        await self.store_session(updated_session)
        return True

    async def get_session_by_client_id(self, client_id: str) -> Optional[UserSession]:
        """Retrieve a session by client ID."""
        for session in self._sessions.values():
            if session.client_id == client_id:
                return await self.get_session(session.session_id)
        return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

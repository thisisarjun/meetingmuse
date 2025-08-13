"""Authentication models for OAuth and session management."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TokenInfo(BaseModel):
    """OAuth token information."""

    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    scopes: List[str] = []


class UserSession(BaseModel):
    """User session information."""

    session_id: str
    client_id: str
    tokens: TokenInfo
    created_at: datetime
    updated_at: datetime

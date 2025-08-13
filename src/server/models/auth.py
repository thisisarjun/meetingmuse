from typing import List, Optional

from pydantic import BaseModel


class AuthUrlResponse(BaseModel):
    """Response model for OAuth authorization URL."""

    authorization_url: str
    state: str
    client_id: str


class CallbackResponse(BaseModel):
    """Response model for OAuth callback."""

    message: str
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    scopes: Optional[List[str]] = None
    success: Optional[bool] = None
    error: Optional[str] = None


class RefreshResponse(BaseModel):
    """Response model for token refresh."""

    message: str
    expires_at: Optional[str] = None


class LogoutResponse(BaseModel):
    """Response model for logout."""

    message: str

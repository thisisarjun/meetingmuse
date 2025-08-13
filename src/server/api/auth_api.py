"""Authentication API endpoints for OAuth flow."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from server.models.auth import (
    AuthUrlResponse,
    CallbackResponse,
    LogoutResponse,
    RefreshResponse,
)
from server.services.oauth_service import oauth_service
from server.services.token_storage import token_storage

logger = logging.getLogger(__name__)


async def start_oauth_flow(client_id: str) -> AuthUrlResponse:
    """
    Start OAuth flow for a client.

    Args:
        client_id: Unique client identifier

    Returns:
        Dictionary containing authorization URL
    """
    try:
        if not client_id or not client_id.strip():
            raise HTTPException(status_code=400, detail="Invalid client_id")

        auth_url, state = await oauth_service.get_authorization_url(client_id)

        logger.info(f"Starting OAuth flow for client: {client_id}")

        return AuthUrlResponse(
            authorization_url=auth_url,
            state=state,
            client_id=client_id,
        )

    except Exception as e:
        logger.error(f"Failed to start OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start OAuth flow")


async def oauth_callback(
    code: Optional[str] = Query(None, description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for security"),
    error: Optional[str] = Query(None, description="Error from OAuth provider"),
) -> CallbackResponse:
    """
    Handle OAuth callback from Google.

    Args:
        code: Authorization code
        state: State parameter
        error: Error parameter (if any)

    Returns:
        Dictionary containing session information
    """
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            return CallbackResponse(
                message=f"OAuth error: {error}",
                error=error,
                success=False,
            )

        if not code or not state:
            raise HTTPException(
                status_code=400, detail="Missing code or state parameter"
            )

        # Process callback
        session = await oauth_service.handle_callback(code, state)

        logger.info(f"OAuth callback successful for client: {session.client_id}")

        return CallbackResponse(
            message="Authentication successful",
            session_id=session.session_id,
            client_id=session.client_id,
            scopes=session.tokens.scopes,
        )

    except ValueError as e:
        logger.error(f"OAuth callback validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


async def refresh_access_token(
    session_id: str = Query(..., description="Session ID")
) -> RefreshResponse:
    """
    Refresh access token using refresh token.

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with refresh status
    """
    try:
        token_info = await oauth_service.refresh_token(session_id)

        if not token_info:
            raise HTTPException(
                status_code=404, detail="Session not found or refresh failed"
            )

        logger.info(f"Token refreshed for session: {session_id}")

        return RefreshResponse(
            message="Token refreshed successfully",
            expires_at=token_info.token_expiry.isoformat()
            if token_info.token_expiry
            else None,
        )

    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


async def logout(client_id: str) -> LogoutResponse:
    """
    Logout and revoke tokens for a client.

    Args:
        client_id: Client identifier

    Returns:
        Dictionary with logout status
    """
    try:
        session = await token_storage.get_session_by_client_id(client_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        success = await oauth_service.revoke_token(session.session_id)

        if success:
            logger.info(f"Logout successful for client: {client_id}")
            return LogoutResponse(message="Logout successful")
        else:
            logger.warning(f"Logout failed for client: {client_id}")
            return LogoutResponse(message="Logout completed (with warnings)")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


def create_auth_router() -> APIRouter:
    """Create and configure authentication API router."""
    router: APIRouter = APIRouter(prefix="/auth", tags=["authentication"])

    # Add routes with proper typing
    router.add_api_route(
        "/login/{client_id}",
        start_oauth_flow,
        methods=["GET"],
        response_model=AuthUrlResponse,
    )
    router.add_api_route(
        "/callback",
        oauth_callback,
        methods=["GET"],
        response_model=CallbackResponse,
    )
    router.add_api_route(
        "/refresh",
        refresh_access_token,
        methods=["POST"],
        response_model=RefreshResponse,
    )
    router.add_api_route(
        "/logout/{client_id}",
        logout,
        methods=["POST"],
        response_model=LogoutResponse,
    )

    return router

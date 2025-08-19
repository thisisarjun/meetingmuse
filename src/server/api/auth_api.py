"""Authentication API endpoints for OAuth flow."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from common.config.config import config
from common.logger.logger import Logger
from server.api.dependencies import get_logger, get_oauth_service, get_session_manager
from server.models.api.auth import (
    AuthUrlResponse,
    LogoutResponse,
    RefreshResponse,
    StatusResponse,
)
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager


async def start_oauth_flow(
    client_id: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
    logger: Logger = Depends(get_logger),
) -> AuthUrlResponse:
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
    oauth_service: OAuthService = Depends(get_oauth_service),
    logger: Logger = Depends(get_logger),
) -> RedirectResponse:
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
            return RedirectResponse(
                url=f"{config.FRONTEND_CALLBACK_URL}?auth_error={error}"
            )

        if not code or not state:
            logger.error("Missing code or state parameter")
            return RedirectResponse(
                url=f"{config.FRONTEND_CALLBACK_URL}?auth_error=missing_parameters"
            )

        session = await oauth_service.handle_callback(code, state)

        logger.info(f"OAuth callback successful for client: {session.client_id}")

        # Redirect to frontend with success
        return RedirectResponse(url=f"{config.FRONTEND_CALLBACK_URL}?auth_success=true")

    except ValueError as e:
        logger.error(f"OAuth callback validation error: {str(e)}")
        return RedirectResponse(
            url=f"{config.FRONTEND_CALLBACK_URL}?auth_error=validation_failed"
        )
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        return RedirectResponse(
            url=f"{config.FRONTEND_CALLBACK_URL}?auth_error=callback_failed"
        )


async def refresh_access_token(
    session_id: str = Query(..., description="Session ID"),
    oauth_service: OAuthService = Depends(get_oauth_service),
    logger: Logger = Depends(get_logger),
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


async def logout(
    client_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    oauth_service: OAuthService = Depends(get_oauth_service),
    logger: Logger = Depends(get_logger),
) -> LogoutResponse:
    """
    Logout and revoke tokens for a client.

    Args:
        client_id: Client identifier

    Returns:
        Dictionary with logout status
    """
    try:
        session = await session_manager.get_session_by_client_id(client_id)
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


async def get_auth_status(
    client_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    oauth_service: OAuthService = Depends(get_oauth_service),
    logger: Logger = Depends(get_logger),
) -> StatusResponse:
    """
    Get authentication status for a client.

    Args:
        client_id: Client identifier

    Returns:
        Dictionary with authentication status
    """
    try:
        if not client_id or not client_id.strip():
            raise HTTPException(status_code=400, detail="Invalid client_id")

        session = await session_manager.get_session_by_client_id(client_id)

        if not session:
            logger.info(f"No session found for client: {client_id}")
            return StatusResponse(
                client_id=client_id, authenticated=False, message="Not authenticated"
            )

        is_valid = await oauth_service.validate_token(session.session_id)

        if not is_valid:
            logger.warning(f"Invalid/expired token for client: {client_id}")
            return StatusResponse(
                client_id=client_id,
                authenticated=False,
                message="Authentication expired",
            )

        updated_session = await session_manager.get_session_by_client_id(client_id)
        if not updated_session:
            return StatusResponse(
                client_id=client_id,
                authenticated=False,
                message="Session not found after validation",
            )

        logger.info(f"Authentication status checked for client: {client_id}")

        return StatusResponse(
            client_id=client_id,
            authenticated=True,
            session_id=updated_session.session_id,
            scopes=updated_session.tokens.scopes,
            token_expires_at=updated_session.tokens.token_expiry.isoformat()
            if updated_session.tokens.token_expiry
            else None,
            message="Authenticated",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check auth status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to check authentication status"
        )


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
        response_model=None,
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
    router.add_api_route(
        "/status/{client_id}",
        get_auth_status,
        methods=["GET"],
        response_model=StatusResponse,
    )

    return router

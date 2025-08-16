"""
WebSocket API
WebSocket endpoints for real-time chat communication with OAuth authentication
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from common.logger import Logger
from server.services.oauth_service import oauth_service

from ..services.websocket_connection_service import WebSocketConnectionService


def create_websocket_router(
    websocket_service: WebSocketConnectionService, logger: Logger
) -> APIRouter:
    """Create and configure WebSocket API router"""
    router = APIRouter(tags=["websocket"])

    @router.websocket("/ws/{client_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        client_id: str,
        session_id: str = Query(..., description="OAuth session ID for authentication"),
    ) -> None:
        """
        Main WebSocket endpoint for authenticated chat conversations

        This endpoint establishes a persistent WebSocket connection for real-time chat
        communication. Each client must provide a unique client_id and valid session_id
        from OAuth authentication to maintain separate conversation contexts.

        ## Authentication

        - **session_id**: Valid OAuth session ID obtained from `/auth/login/{client_id}` flow
        - Connection will be rejected if session_id is invalid or expired
        - Tokens are automatically refreshed during the connection lifetime

        ## Message Format

        Clients should send JSON messages in the following format:
        ```json
        {
            "type": "user_message",
            "content": "Your message here",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```

        ## Response Format

        The server responds with various message types:

        **User Messages Echo**:
        ```json
        {
            "type": "user_message",
            "content": "Your message",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```

        **AI Responses**:
        ```json
        {
            "type": "assistant_message",
            "content": "AI response here",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```

        **System Messages**:
        ```json
        {
            "type": "system_message",
            "content": "Connection established",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```

        **Error Messages**:
        ```json
        {
            "type": "error",
            "error_code": "INVALID_FORMAT",
            "message": "Invalid message format",
            "retry_suggested": true,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        ```

        ## Parameters

        - **client_id**: Unique identifier for the client session (path parameter)
          - Must be a non-empty string
          - Used to maintain conversation context
          - Should be unique per user session
        - **session_id**: OAuth session ID for authentication (query parameter)
          - Must be a valid session ID from successful OAuth flow
          - Used to validate user authentication and access tokens

        """
        # Validate authentication first
        if not session_id or not session_id.strip():
            logger.warning(f"Missing session_id for client: {client_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Missing session_id"
            )

        # Validate the OAuth session
        is_valid = await oauth_service.validate_token(session_id)
        if not is_valid:
            logger.warning(f"Invalid or expired session_id for client: {client_id}")
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
            raise WebSocketException(
                code=status.WS_1003_UNSUPPORTED_DATA,
                reason="Invalid or expired session",
            )

        # Validate client ID
        if not client_id or not client_id.strip():
            logger.warning(f"Invalid client_id: {client_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid client_id"
            )

        logger.info(f"Authenticated WebSocket connection for client: {client_id}")
        await websocket_service.handle_websocket_connection(
            websocket, client_id, session_id
        )

    return router

"""
WebSocket API
WebSocket endpoints for real-time chat communication
"""
import logging

from fastapi import APIRouter, WebSocket, WebSocketException, status

from ..services.websocket_connection_service import WebSocketConnectionService

logger = logging.getLogger(__name__)


def create_websocket_router(websocket_service: WebSocketConnectionService) -> APIRouter:
    """Create and configure WebSocket API router"""
    router = APIRouter(tags=["websocket"])

    @router.websocket("/ws/{client_id}")  # type: ignore[misc]
    async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
        """
        Main WebSocket endpoint for chat conversations

        This endpoint establishes a persistent WebSocket connection for real-time chat
        communication. Each client must provide a unique client_id to maintain
        separate conversation contexts.

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

        """
        if not client_id or not client_id.strip():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid client_id"
            )

        await websocket_service.handle_websocket_connection(websocket, client_id)

    return router

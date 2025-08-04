"""
WebSocket API
WebSocket endpoints for real-time chat communication
"""
import logging

from fastapi import APIRouter, WebSocket

from ..services.websocket_connection_handler import WebSocketConnectionService

logger = logging.getLogger(__name__)


def create_websocket_router(websocket_service: WebSocketConnectionService) -> APIRouter:
    """Create and configure WebSocket API router"""
    router = APIRouter(tags=["websocket"])

    @router.websocket("/ws/{client_id}")  # type: ignore
    async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
        """
        Main WebSocket endpoint for chat conversations

        Args:
            websocket: WebSocket connection object
            client_id: Unique identifier for the client session
        """
        await websocket_service.handle_websocket_connection(websocket, client_id)

    return router

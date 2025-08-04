"""
WebSocket Connection Manager
Handles WebSocket connections, client management, and message broadcasting
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from .constants import SystemMessageTypes

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for the chat application"""

    def __init__(self) -> None:
        # Dictionary to store active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Accept a new WebSocket connection and add it to active connections

        Args:
            websocket: The WebSocket connection object
            client_id: Unique identifier for the client

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": datetime.now().isoformat(),
                "message_count": 0,
            }

            logger.info(f"Client {client_id} connected successfully")

            # Send connection confirmation
            await self.send_system_message(
                client_id, SystemMessageTypes.CONNECTION_ESTABLISHED
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {str(e)}")
            return False

    def disconnect(self, client_id: str) -> bool:
        """
        Remove a client from active connections

        Args:
            client_id: Unique identifier for the client

        Returns:
            bool: True if client was found and removed, False otherwise
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

            if client_id in self.connection_metadata:
                metadata = self.connection_metadata.pop(client_id)
                logger.info(
                    f"Client {client_id} disconnected. "
                    f"Messages processed: {metadata.get('message_count', 0)}"
                )

            return True
        return False

    async def send_personal_message(self, message: str, client_id: str) -> bool:
        """
        Send a message to a specific client

        Args:
            message: Message content to send
            client_id: Target client identifier

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            logger.warning(
                f"Attempted to send message to disconnected client: {client_id}"
            )
            return False

        try:
            websocket = self.active_connections[client_id]

            # Format message according to protocol
            response = {
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "session_id": client_id,
            }

            await websocket.send_text(json.dumps(response))
            logger.debug(f"Message sent to client {client_id}: {message[:50]}...")
            return True

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during message send")
            self.disconnect(client_id)
            return False
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}")
            return False

    async def send_system_message(self, client_id: str, system_type: str) -> bool:
        """
        Send a system message to a specific client

        Args:
            client_id: Target client identifier
            system_type: Type of system message (see SystemMessageTypes constants)

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]

            system_message = {
                "type": "system",
                "content": system_type,
                "timestamp": datetime.now().isoformat(),
            }

            await websocket.send_text(json.dumps(system_message))
            return True

        except Exception as e:
            logger.error(
                f"Failed to send system message to client {client_id}: {str(e)}"
            )
            return False

    async def send_error_message(
        self,
        client_id: str,
        error_code: str,
        message: str,
        retry_suggested: bool = True,
    ) -> bool:
        """
        Send an error message to a specific client

        Args:
            client_id: Target client identifier
            error_code: Error code identifier
            message: Human-readable error message
            retry_suggested: Whether client should retry the operation

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]

            error_response = {
                "type": "error",
                "error_code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "retry_suggested": retry_suggested,
            }

            await websocket.send_text(json.dumps(error_response))
            return True

        except Exception as e:
            logger.error(
                f"Failed to send error message to client {client_id}: {str(e)}"
            )
            return False

    async def broadcast(self, message: str) -> int:
        """
        Send a message to all connected clients

        Args:
            message: Message content to broadcast

        Returns:
            int: Number of clients that successfully received the message
        """
        successful_sends = 0
        failed_clients = []

        for client_id in list(self.active_connections.keys()):
            success = await self.send_personal_message(message, client_id)
            if success:
                successful_sends += 1
            else:
                failed_clients.append(client_id)

        # Clean up failed connections
        for client_id in failed_clients:
            self.disconnect(client_id)

        logger.info(
            f"Broadcast sent to {successful_sends} clients, {len(failed_clients)} failed"
        )
        return successful_sends

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_client_info(self, client_id: str) -> Optional[dict]:
        """Get metadata for a specific client"""
        return self.connection_metadata.get(client_id)

    def list_active_clients(self) -> List[str]:
        """Get list of all active client IDs"""
        return list(self.active_connections.keys())

    def increment_message_count(self, client_id: str) -> None:
        """Increment message count for a client"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["message_count"] += 1

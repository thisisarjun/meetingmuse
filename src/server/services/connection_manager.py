"""
WebSocket Connection Manager
Handles WebSocket connections, client management, and message broadcasting
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from server.models.api.web_socket_message import (
    BotResponse,
    ErrorMessage,
    SystemMessage,
)

from ..constants import SystemMessageTypes
from ..models.connections import ConnectionMetadataDto

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for the chat application"""

    def __init__(self) -> None:
        # Dictionary to store active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, ConnectionMetadataDto] = {}

    async def connect(
        self, websocket: WebSocket, client_id: str, session_id: Optional[str] = None
    ) -> bool:
        """
        Accept a new WebSocket connection and add it to active connections

        Args:
            websocket: The WebSocket connection object
            client_id: Unique identifier for the client
            session_id: Optional OAuth session ID for authenticated connections

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = ConnectionMetadataDto(
                connected_at=datetime.now().isoformat(),
                message_count=0,
            )

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
                    f"Messages processed: {metadata.message_count}"
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
            response = BotResponse(
                content=message,
                session_id=client_id,
            )

            await websocket.send_text(response.model_dump_json())
            logger.debug(f"Message sent to client {client_id}: {message[:50]}...")
            return True

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during message send")
            self.disconnect(client_id)
            return False
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}")
            return False

    async def send_system_message(
        self,
        client_id: str,
        system_type: SystemMessageTypes,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a system message to a specific client

        Args:
            client_id: Target client identifier
            system_type: Type of system message (see SystemMessageTypes constants)
            additional_data: Optional additional data to include in the message

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]

            # TODO: system message has to be pydantic model
            system_message = SystemMessage(
                content=system_type,
            )

            # Add additional data if provided
            if additional_data:
                system_message.metadata = additional_data

            await websocket.send_text(system_message.model_dump_json())
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
        content: str,
        retry_suggested: bool = True,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an error message to a specific client

        Args:
            client_id: Target client identifier
            error_code: Error code identifier
            content: Human-readable error message
            retry_suggested: Whether client should retry the operation
            additional_metadata: Optional additional metadata to include

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]

            error_response = ErrorMessage(
                error_code=error_code,
                content=content,
                retry_suggested=retry_suggested,
            )

            # Add additional metadata if provided
            if additional_metadata:
                error_response.metadata = additional_metadata

            await websocket.send_text(error_response.model_dump_json())
            return True

        except Exception as e:
            logger.error(
                f"Failed to send error message to client {client_id}: {str(e)}"
            )
            return False

    def get_client_info(self, client_id: str) -> Optional[ConnectionMetadataDto]:
        """Get metadata for a specific client"""
        return self.connection_metadata.get(client_id)

    def list_active_clients(self) -> List[str]:
        """Get list of all active client IDs"""
        return list(self.active_connections.keys())

    def increment_message_count(self, client_id: str) -> None:
        """Increment message count for a client"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id].message_count += 1

    def get_active_connections(self) -> int:
        """Get statistics about WebSocket connections"""
        active_connections = self.active_connections.keys()
        return len(active_connections)

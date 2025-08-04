"""
Admin Service
Business logic for administrative operations and management
"""
import logging
from datetime import datetime
from typing import Any, Dict

from .connection_manager import ConnectionManager
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class AdminService:
    """Service for handling administrative operations"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_manager: ConversationManager,
    ) -> None:
        self.connection_manager = connection_manager
        self.conversation_manager = conversation_manager

    async def broadcast_message(self, content: str) -> Dict[str, Any]:
        """Broadcast a message to all connected clients"""
        logger.info(f"Broadcasting message to all clients: {content[:50]}...")

        successful_sends = await self.connection_manager.broadcast(content)

        logger.info(f"Broadcast completed. Successful sends: {successful_sends}")

        return {
            "status": "success",
            "message": "Broadcast completed",
            "successful_sends": successful_sends,
            "timestamp": datetime.now().isoformat(),
        }

    def get_connections_info(self) -> Dict[str, Any]:
        """Get detailed information about active connections"""
        active_clients = self.connection_manager.list_active_clients()
        client_info = {}

        for client_id in active_clients:
            client_info[client_id] = self.connection_manager.get_client_info(client_id)

        return {
            "active_connections": self.connection_manager.get_connection_count(),
            "clients": client_info,
            "timestamp": datetime.now().isoformat(),
        }

    def get_conversations_info(self) -> Dict[str, Any]:
        """Get detailed information about active conversations"""
        active_conversations = self.conversation_manager.list_active_conversations()

        return {
            "active_conversations": self.conversation_manager.get_active_conversation_count(),
            "conversation_clients": active_conversations,
            "timestamp": datetime.now().isoformat(),
        }

    async def disconnect_client(self, client_id: str) -> Dict[str, Any]:
        """Administratively disconnect a specific client"""
        logger.info(f"Admin disconnect requested for client: {client_id}")

        if client_id not in self.connection_manager.list_active_clients():
            return {
                "status": "error",
                "message": f"Client {client_id} not found or already disconnected",
                "timestamp": datetime.now().isoformat(),
            }

        # Notify client before disconnecting
        await self.connection_manager.send_system_message(
            client_id,
            "admin_disconnect",
            additional_data={"reason": "Administrative disconnect"},
        )

        # Disconnect and clean up
        self.connection_manager.disconnect(client_id)
        await self.conversation_manager.end_conversation(client_id)

        logger.info(f"Client {client_id} disconnected by admin")

        return {
            "status": "success",
            "message": f"Client {client_id} has been disconnected",
            "timestamp": datetime.now().isoformat(),
        }

    async def send_message_to_client(
        self, client_id: str, message: str
    ) -> Dict[str, Any]:
        """Send a direct message to a specific client"""
        logger.info(f"Admin message to {client_id}: {message[:50]}...")

        if client_id not in self.connection_manager.list_active_clients():
            return {
                "status": "error",
                "message": f"Client {client_id} not found or not connected",
                "timestamp": datetime.now().isoformat(),
            }

        success = await self.connection_manager.send_personal_message(
            message, client_id
        )

        if success:
            logger.info(f"Admin message sent successfully to {client_id}")
            return {
                "status": "success",
                "message": f"Message sent to client {client_id}",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error(f"Failed to send admin message to {client_id}")
            return {
                "status": "error",
                "message": f"Failed to send message to client {client_id}",
                "timestamp": datetime.now().isoformat(),
            }

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics for admin dashboard"""
        active_clients = self.connection_manager.list_active_clients()

        # Collect client statistics
        total_messages = 0
        connection_times = []

        for client_id in active_clients:
            client_info = self.connection_manager.get_client_info(client_id)
            if client_info:
                total_messages += client_info.get("message_count", 0)
                if "connected_at" in client_info:
                    connection_times.append(client_info["connected_at"])

        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_active_connections": len(active_clients),
                "total_active_conversations": self.conversation_manager.get_active_conversation_count(),
                "total_messages_processed": total_messages,
            },
            "connection_statistics": {
                "average_messages_per_client": total_messages / len(active_clients)
                if active_clients
                else 0,
                "recent_connections": connection_times[-10:]
                if connection_times
                else [],
            },
        }

    async def cleanup_connections(self) -> Dict[str, Any]:
        """Clean up all active connections (for admin use)"""
        logger.info("Admin-initiated cleanup of all connections")

        active_clients = self.connection_manager.list_active_clients()
        if not active_clients:
            return {
                "status": "success",
                "message": "No active connections to clean up",
                "cleaned_connections": 0,
                "timestamp": datetime.now().isoformat(),
            }

        # Notify all clients before cleanup
        await self.connection_manager.broadcast(
            "Server maintenance in progress. Please reconnect shortly."
        )

        # Clean up all connections
        cleaned_count = 0
        for client_id in active_clients.copy():
            self.connection_manager.disconnect(client_id)
            await self.conversation_manager.end_conversation(client_id)
            cleaned_count += 1

        logger.info(f"Admin cleanup completed. {cleaned_count} connections cleaned up")

        return {
            "status": "success",
            "message": "All connections cleaned up successfully",
            "cleaned_connections": cleaned_count,
            "timestamp": datetime.now().isoformat(),
        }

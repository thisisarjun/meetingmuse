"""
Health Service
Business logic for system health checks and monitoring
"""
import logging
from datetime import datetime
from typing import Any, Dict

from ..langgraph.message_processor import LangGraphMessageProcessor
from ..langgraph.streaming_handler import StreamingHandler
from .connection_manager import ConnectionManager
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class HealthService:
    """Service for handling health checks and system monitoring"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_manager: ConversationManager,
        message_processor: LangGraphMessageProcessor,
        streaming_handler: StreamingHandler,
    ) -> None:
        self.connection_manager = connection_manager
        self.conversation_manager = conversation_manager
        self.message_processor = message_processor
        self.streaming_handler = streaming_handler

    def get_health_status(self) -> Dict[str, Any]:
        """Get the basic health status of the system"""
        processor_ready = (
            self.message_processor.is_ready() if self.message_processor else False
        )
        streaming_ready = (
            self.streaming_handler.is_ready() if self.streaming_handler else False
        )

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": self.connection_manager.get_connection_count(),
            "active_conversations": self.conversation_manager.get_active_conversation_count(),
            "langgraph_processor_ready": processor_ready,
            "streaming_handler_ready": streaming_ready,
        }

    def get_detailed_health_status(self) -> Dict[str, Any]:
        """Get detailed health status with connection information"""
        base_status = self.get_health_status()

        # Add detailed information
        detailed_info = {
            "active_clients": self.connection_manager.list_active_clients(),
            "conversation_clients": self.conversation_manager.list_active_conversations(),
        }

        return {**base_status, **detailed_info}

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        active_clients = self.connection_manager.list_active_clients()

        # Calculate average messages per client
        total_messages = 0
        client_details = {}

        for client_id in active_clients:
            client_info = self.connection_manager.get_client_info(client_id)
            if client_info:
                message_count = client_info.get("message_count", 0)
                total_messages += message_count
                client_details[client_id] = {
                    "message_count": message_count,
                    "connected_at": client_info.get("connected_at"),
                }

        avg_messages = total_messages / len(active_clients) if active_clients else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "connections": {
                "total_active": len(active_clients),
                "total_messages": total_messages,
                "average_messages_per_client": round(avg_messages, 2),
            },
            "conversations": {
                "total_active": self.conversation_manager.get_active_conversation_count(),
            },
            "services": {
                "langgraph_processor_ready": (
                    self.message_processor.is_ready()
                    if self.message_processor
                    else False
                ),
                "streaming_handler_ready": (
                    self.streaming_handler.is_ready()
                    if self.streaming_handler
                    else False
                ),
            },
            "client_details": client_details,
        }

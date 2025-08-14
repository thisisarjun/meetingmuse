"""
Health Service
Business logic for system health checks and monitoring
"""
import logging
from typing import Any, Dict

from meetingmuse.graph.graph_message_processor import GraphMessageProcessor

from .connection_manager import ConnectionManager
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class HealthService:
    """Service for handling health checks and system monitoring"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_manager: ConversationManager,
        message_processor: GraphMessageProcessor,
    ) -> None:
        self.connection_manager = connection_manager
        self.conversation_manager = conversation_manager
        self.message_processor = message_processor

    def get_health_status(self) -> Dict[str, Any]:
        """Get the basic health status of the system"""
        processor_ready = (
            self.message_processor.is_ready() if self.message_processor else False
        )

        return {
            "status": "healthy",
            "active_connections": self.connection_manager.get_connection_count(),
            "active_conversations": self.conversation_manager.get_active_conversation_count(),
            "langgraph_processor_ready": processor_ready,
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        active_clients = self.connection_manager.list_active_clients()

        # Calculate average messages per client
        total_messages = 0

        for client_id in active_clients:
            client_info = self.connection_manager.get_client_info(client_id)
            if client_info:
                message_count = client_info.message_count
                total_messages += message_count

        avg_messages = total_messages / len(active_clients) if active_clients else 0

        return {
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
            },
            "client_details": client_info,
        }

"""
Conversation Manager for WebSocket Server
Handles conversation state and recovery for WebSocket connections
"""
from datetime import datetime
from typing import Dict, Optional

from common.logger.logger import Logger
from meetingmuse.graph.graph_message_processor import GraphMessageProcessor
from server.models.conversation import ActiveConversation, ConversationStatus


class ConversationManager:
    """Manages conversation state and recovery for WebSocket connections"""

    def __init__(
        self, logger: Logger, message_processor: GraphMessageProcessor
    ) -> None:
        self.logger = logger
        self.message_processor = message_processor
        self.active_conversations: Dict[str, ActiveConversation] = {}

    def initialize_conversation(
        self, client_id: str, session_id: Optional[str] = None
    ) -> bool:
        """
        Initialize conversation state for a new client

        Args:
            client_id: Client identifier
            session_id: Optional OAuth session ID for authenticated conversations

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if client_id not in self.active_conversations:
                self.active_conversations[client_id] = ActiveConversation(
                    started_at=datetime.now().isoformat(),
                    last_activity=datetime.now().isoformat(),
                    message_count=0,
                    status=ConversationStatus.ACTIVE,
                    session_id=session_id,
                    authenticated=session_id is not None,
                )
                self.logger.info(f"Initialized conversation for client {client_id}")

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to initialize conversation for client {client_id}: {str(e)}"
            )
            return False

    async def handle_reconnection(self, client_id: str) -> bool:
        """
        Handle conversation recovery after reconnection

        Args:
            client_id: Client identifier

        Returns:
            True if conversation recovered, False otherwise
        """
        try:
            # Get current conversation state from LangGraph
            has_conversation = await self.message_processor.get_conversation_state(
                client_id
            )
            if has_conversation:
                # Update conversation metadata
                if client_id in self.active_conversations:
                    self.active_conversations[
                        client_id
                    ].last_activity = datetime.now().isoformat()
                    self.active_conversations[
                        client_id
                    ].status = ConversationStatus.RESUMED

                self.logger.info(f"Conversation recovered for client {client_id}")
                return True

            # No existing conversation found
            return False

        except Exception as e:
            self.logger.error(
                f"Error handling reconnection for client {client_id}: {str(e)}"
            )
            return False

    def update_conversation_activity(self, client_id: str) -> None:
        """
        Update conversation activity timestamp

        Args:
            client_id: Client identifier
        """
        if client_id in self.active_conversations:
            self.active_conversations[
                client_id
            ].last_activity = datetime.now().isoformat()
            self.active_conversations[client_id].message_count += 1

    async def end_conversation(self, client_id: str) -> None:
        """
        Mark conversation as ended and cleanup

        Args:
            client_id: Client identifier
        """
        try:
            if client_id in self.active_conversations:
                self.active_conversations[client_id].status = ConversationStatus.ENDED
                self.active_conversations[
                    client_id
                ].ended_at = datetime.now().isoformat()

                # Optional: Remove old conversations after some time
                # For now, we'll keep them for potential analysis

                self.logger.info(f"Conversation ended for client {client_id}")

        except Exception as e:
            self.logger.error(
                f"Error ending conversation for client {client_id}: {str(e)}"
            )

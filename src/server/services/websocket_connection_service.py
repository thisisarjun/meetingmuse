"""
WebSocket Connection Service
Core business logic for WebSocket connection handling and message processing
"""
import logging
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect, status

from ..constants import CloseReasons, ErrorCodes, ErrorMessages, SystemMessageTypes
from ..langgraph.message_processor import LangGraphMessageProcessor
from ..langgraph.streaming_handler import StreamingHandler
from ..models.ws_dtos import MessageProtocol
from .connection_manager import ConnectionManager
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class WebSocketConnectionService:
    """Service for handling WebSocket connections and message processing"""

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

    async def handle_websocket_connection(
        self, websocket: WebSocket, client_id: str, session_id: str
    ) -> None:
        """
        Handle the complete WebSocket connection lifecycle for an authenticated client

        Args:
            websocket: WebSocket connection object
            client_id: Unique identifier for the client session
            session_id: OAuth session identifier for authentication
        """

        # Attempt to establish connection
        connection_success = await self.connection_manager.connect(
            websocket, client_id, session_id
        )
        if not connection_success:
            logger.error(f"Failed to establish connection for client: {client_id}")
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=CloseReasons.CONNECTION_ESTABLISHMENT_FAILED,
            )
            return

        logger.info(f"WebSocket connection established for client: {client_id}")

        # Initialize conversation
        await self.conversation_manager.initialize_conversation(client_id, session_id)

        # Handle potential reconnection and conversation recovery
        recovery_info = await self.conversation_manager.handle_reconnection(client_id)
        if recovery_info and recovery_info.get("conversation_resumed"):
            await self.connection_manager.send_system_message(
                client_id, "conversation_resumed", additional_data=recovery_info
            )

        try:
            await self._handle_message_loop(websocket, client_id)
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(
                f"Error handling WebSocket connection for {client_id}: {str(e)}"
            )
            # Attempt to send error message before closing
            try:
                await self.connection_manager.send_error_message(
                    client_id,
                    ErrorCodes.INTERNAL_SERVER_ERROR,
                    ErrorMessages.INTERNAL_SERVER_ERROR,
                    retry_suggested=True,
                )
            except Exception:
                logger.warning(
                    f"Could not send error message to {client_id} before cleanup"
                )
        finally:
            # Clean up connection and conversation
            await self._cleanup_client_connection(client_id)

    async def _handle_message_loop(self, websocket: WebSocket, client_id: str) -> None:
        """Handle the message processing loop for a client"""
        logger.debug(f"Starting message loop for client: {client_id}")

        while True:
            message_text = await websocket.receive_text()
            self.connection_manager.increment_message_count(client_id)

            # Parse the incoming message
            user_message = MessageProtocol.parse_user_message(message_text)

            if user_message is None:
                logger.warning(f"Invalid message format from {client_id}")
                await self.connection_manager.send_error_message(
                    client_id,
                    ErrorCodes.INVALID_MESSAGE_FORMAT,
                    ErrorMessages.INVALID_MESSAGE_FORMAT,
                    retry_suggested=True,
                )
                continue

            # TODO: Remove in next iteration
            logger.info(
                f"Received message from {client_id}: {user_message.content[:100]}..."
            )

            # Send processing notification
            await self.connection_manager.send_system_message(
                client_id, SystemMessageTypes.PROCESSING
            )

            # Update conversation activity
            await self.conversation_manager.update_conversation_activity(client_id)

            # Process the message
            try:
                response_content = await self._process_user_message(
                    client_id, user_message.content
                )

                # Send AI response
                success = await self.connection_manager.send_personal_message(
                    response_content, client_id
                )

                if not success:
                    logger.warning(f"Failed to send response to client {client_id}")
                    break

            except Exception as llm_error:
                logger.error(
                    f"LLM processing error for client {client_id}: {str(llm_error)}"
                )
                await self._handle_processing_error(client_id, llm_error)

    async def _process_user_message(self, client_id: str, message_content: str) -> str:
        """Process a user message and return the response"""
        # Check for any pending interrupts first
        interrupt_info = await self.message_processor.handle_interrupts(client_id)

        if interrupt_info and interrupt_info.get("waiting_for_input"):
            # Handle interrupt - ask for user input
            interrupt_notification = (
                await self.streaming_handler.create_interrupt_notification(
                    interrupt_info, client_id
                )
            )
            await self.connection_manager.send_system_message(
                client_id,
                "waiting_for_input",
                additional_data=interrupt_notification,
            )

            # Resume conversation with user input
            response_content = await self.message_processor.resume_conversation(
                client_id, message_content
            )
        else:
            # Process normal message
            response_content = await self.message_processor.process_user_message(
                message_content, client_id
            )

        return response_content

    async def _handle_processing_error(self, client_id: str, error: Exception) -> None:
        """Handle errors during message processing"""
        await self.connection_manager.send_error_message(
            client_id,
            ErrorCodes.INTERNAL_SERVER_ERROR,
            "I'm having trouble processing your request. Please try again.",
            retry_suggested=True,
            additional_metadata={
                "conversation_preserved": True,
                "fallback_available": True,
                "error_type": type(error).__name__,
            },
        )

    async def _cleanup_client_connection(self, client_id: str) -> None:
        """Clean up a client's connection and conversation"""
        logger.info(f"Cleaning up connection for client: {client_id}")

        # Disconnect from connection manager
        self.connection_manager.disconnect(client_id)

        # End conversation
        await self.conversation_manager.end_conversation(client_id)

        logger.info(f"Connection cleanup completed for client: {client_id}")

    async def cleanup_all_connections(self) -> None:
        """Clean up all active connections during shutdown"""
        active_clients = self.connection_manager.list_active_clients()
        if active_clients:
            logger.info(f"Cleaning up {len(active_clients)} active connections")
            for client_id in active_clients.copy():
                await self._cleanup_client_connection(client_id)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about WebSocket connections"""
        active_clients = self.connection_manager.list_active_clients()
        total_messages = 0

        for client_id in active_clients:
            client_info = self.connection_manager.get_client_info(client_id)
            if client_info:
                total_messages += client_info.get("message_count", 0)

        return {
            "active_connections": len(active_clients),
            "total_messages_processed": total_messages,
            "average_messages_per_connection": (
                total_messages / len(active_clients) if active_clients else 0
            ),
        }

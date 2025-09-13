"""
WebSocket Connection Service
Core business logic for WebSocket connection handling and message processing
"""
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, status

from common.logger.logger import Logger
from meetingmuse.graph.graph_message_processor import GraphMessageProcessor
from server.models.api.ws import UserMessage
from server.services.message_processor import MessageProtocol

from ..constants import CloseReasons, ErrorCodes, ErrorMessages, SystemMessageTypes
from .connection_manager import ConnectionManager
from .conversation_manager import ConversationManager


class WebSocketConnectionService:
    """Service for handling WebSocket connections and message processing"""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        conversation_manager: ConversationManager,
        graph_message_processor: GraphMessageProcessor,
        logger: Logger,
    ) -> None:
        self.connection_manager = connection_manager
        self.conversation_manager = conversation_manager
        self.graph_message_processor = graph_message_processor
        self.logger = logger

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
            self.logger.error(f"Failed to establish connection for client: {client_id}")
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=CloseReasons.CONNECTION_ESTABLISHMENT_FAILED,
            )
            return

        self.logger.info(f"WebSocket connection established for client: {client_id}")

        # Initialize conversation
        self.conversation_manager.initialize_conversation(client_id, session_id)

        # Handle potential reconnection and conversation recovery
        conversation_resumed = await self.conversation_manager.handle_reconnection(
            client_id
        )
        if conversation_resumed:
            await self.connection_manager.send_system_message(
                client_id,
                SystemMessageTypes.CONVERSATION_RESUMED,
            )

        try:
            await self._handle_message_loop(websocket, client_id)
        except WebSocketDisconnect:
            self.logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            self.logger.error(
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
                self.logger.warning(
                    f"Could not send error message to {client_id} before cleanup"
                )
        finally:
            # Clean up connection and conversation
            await self._cleanup_client_connection(client_id)

    async def _handle_message_loop(self, websocket: WebSocket, client_id: str) -> None:
        """Handle the message processing loop for a client"""
        self.logger.debug(f"Starting message loop for client: {client_id}")

        while True:
            message_text = await websocket.receive_text()
            self.connection_manager.increment_message_count(client_id)

            # Parse the incoming message
            user_message: Optional[UserMessage] = None
            try:
                user_message = MessageProtocol.parse_user_message(message_text)
            except Exception as e:
                self.logger.error(f"Error parsing user message: {str(e)}")
                self.logger.warning(f"Invalid message format from {client_id}")
                await self.connection_manager.send_error_message(
                    client_id,
                    ErrorCodes.INVALID_MESSAGE_FORMAT,
                    ErrorMessages.INVALID_MESSAGE_FORMAT,
                    retry_suggested=True,
                )
                continue

            # TODO: Remove in next iteration
            self.logger.info(f"Received message from {client_id}")

            # Send processing notification
            await self.connection_manager.send_system_message(
                client_id, SystemMessageTypes.PROCESSING
            )

            # Update conversation activity
            self.conversation_manager.update_conversation_activity(client_id)

            # Process the message
            try:
                response_content = await self._process_input_user_message(
                    client_id, user_message.content
                )

                # Send AI response
                success = await self.connection_manager.send_personal_message(
                    response_content, client_id
                )

                if not success:
                    self.logger.warning(
                        f"Failed to send response to client {client_id}"
                    )
                    break

            except Exception as llm_error:
                self.logger.error(
                    f"LLM processing error for client {client_id}: {str(llm_error)}"
                )
                await self._handle_processing_error(client_id, llm_error)

    async def _process_input_user_message(
        self, client_id: str, message_content: str
    ) -> str:
        """Process a user message and return the response"""
        # Check for any pending interrupts first
        interrupt_info = await self.graph_message_processor.check_if_interrupt_exists(
            client_id
        )
        self.logger.info(f"Interrupt detected: {interrupt_info}")
        if interrupt_info:
            self.logger.info("waiting for input")
            # Handle interrupt - ask for user input

            # Resume conversation with user input
            response_content = (
                await self.graph_message_processor.resume_interrupt_conversation(
                    client_id, message_content
                )
            )
        else:
            # Process normal message
            session_id = self.conversation_manager.get_session_id(client_id)
            if session_id is None:
                raise ConnectionRefusedError("Session ID is missing for user")

            response_content = await self.graph_message_processor.process_user_message(
                message_content, client_id, session_id
            )

        self.logger.info(f"Response content: {response_content}")
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
        self.logger.info(f"Cleaning up connection for client: {client_id}")

        # Disconnect from connection manager
        self.connection_manager.disconnect(client_id)

        # End conversation
        await self.conversation_manager.end_conversation(client_id)

        self.logger.info(f"Connection cleanup completed for client: {client_id}")

    async def cleanup_all_connections(self) -> None:
        """Clean up all active connections during shutdown"""
        active_clients = self.connection_manager.list_active_clients()
        if active_clients:
            self.logger.info(f"Cleaning up {len(active_clients)} active connections")
            for client_id in active_clients.copy():
                await self._cleanup_client_connection(client_id)

"""
WebSocket Routes
FastAPI WebSocket endpoint definitions and health checks
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
from datetime import datetime

from ..services.connection_manager import ConnectionManager
from ..models.message_protocol import MessageProtocol
from ..constants import ErrorCodes, ErrorMessages, WebSocketCloseCodes, CloseReasons, SystemMessageTypes
from ..services.conversation_manager import ConversationManager
from ..langgraph.message_processor import LangGraphMessageProcessor
from ..handlers.streaming_handler import StreamingHandler

logger = logging.getLogger(__name__)

# Global connection manager instance
connection_manager = ConnectionManager()

# Global conversation manager instance  
conversation_manager = ConversationManager()

# Global message processor instance
message_processor = LangGraphMessageProcessor()

# Global streaming handler instance
streaming_handler = StreamingHandler()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="MeetingMuse WebSocket Server",
        description="WebSocket server for MeetingMuse chat application",
        version="1.0.0"
    )
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        processor_ready = message_processor.is_ready() if message_processor else False
        streaming_ready = streaming_handler.is_ready() if streaming_handler else False
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": connection_manager.get_connection_count(),
            "active_conversations": conversation_manager.get_active_conversation_count(),
            "langgraph_processor_ready": processor_ready,
            "streaming_handler_ready": streaming_ready
        })
    
    @app.get("/health/clients")
    async def detailed_health_check():
        """Detailed health check with connection information"""
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": connection_manager.get_connection_count(),
            "active_clients": connection_manager.list_active_clients(),
            "active_conversations": conversation_manager.get_active_conversation_count(),
            "conversation_clients": conversation_manager.list_active_conversations(),
        })
    
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """
        Main WebSocket endpoint for chat conversations
        
        Args:
            websocket: WebSocket connection object
            client_id: Unique identifier for the client session
        """
        # Validate client ID TODO: Use JWT validation
        if not MessageProtocol.validate_client_id(client_id):
            await websocket.close(code=WebSocketCloseCodes.POLICY_VIOLATION, reason=CloseReasons.INVALID_CLIENT_ID)
            return
        
        connection_success = await connection_manager.connect(websocket, client_id)
        if not connection_success:
            await websocket.close(code=WebSocketCloseCodes.INTERNAL_ERROR, reason=CloseReasons.CONNECTION_ESTABLISHMENT_FAILED)
            return
        
        logger.info(f"WebSocket connection established for client: {client_id}")
        
        await conversation_manager.initialize_conversation(client_id)
        
        # Handle potential reconnection and conversation recovery
        recovery_info = await conversation_manager.handle_reconnection(client_id)
        if recovery_info and recovery_info.get("conversation_resumed"):
            await connection_manager.send_system_message(
                client_id, 
                "conversation_resumed",
                additional_data=recovery_info
            )
        
        try:
            while True:
                message_text = await websocket.receive_text()
                connection_manager.increment_message_count(client_id)
                # TODO: Remove in next iteration
                logger.info(f"Received message from {client_id}: {message_text[:100]}...")
                
                user_message = MessageProtocol.parse_user_message(message_text)
                
                if user_message is None:
                    await connection_manager.send_error_message(
                        client_id,
                        ErrorCodes.INVALID_MESSAGE_FORMAT,
                        ErrorMessages.INVALID_MESSAGE_FORMAT,
                        retry_suggested=True
                    )
                    continue
                
                await connection_manager.send_system_message(client_id, SystemMessageTypes.PROCESSING)
                
                await conversation_manager.update_conversation_activity(client_id)
                
                try:
                    # Check for any pending interrupts first
                    interrupt_info = await message_processor.handle_interrupts(client_id)
                    
                    if interrupt_info and interrupt_info.get("waiting_for_input"):
                        # Handle interrupt - ask for user input
                        interrupt_notification = await streaming_handler.create_interrupt_notification(
                            interrupt_info, client_id
                        )
                        await connection_manager.send_system_message(
                            client_id,
                            "waiting_for_input", 
                            additional_data=interrupt_notification
                        )
                        
                        # Resume conversation with user input
                        response_content = await message_processor.resume_conversation(
                            client_id, user_message.content
                        )
                    else:
                        response_content = await message_processor.process_user_message(
                            user_message.content, client_id
                        )
                    
                    # Send AI response
                    success = await connection_manager.send_personal_message(response_content, client_id)
                    
                    if not success:
                        logger.warning(f"Failed to send response to client {client_id}")
                        break
                
                except Exception as llm_error:
                    logger.error(f"LLM processing error for client {client_id}: {str(llm_error)}")
                    await connection_manager.send_error_message(
                        client_id,
                        ErrorCodes.INTERNAL_SERVER_ERROR,
                        "I'm having trouble processing your request. Please try again.",
                        retry_suggested=True,
                        additional_metadata={
                            "conversation_preserved": True,
                            "fallback_available": True
                        }
                    )
                
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection for {client_id}: {str(e)}")
            # Attempt to send error message before closing
            try:
                await connection_manager.send_error_message(
                    client_id,
                    ErrorCodes.INTERNAL_SERVER_ERROR,
                    ErrorMessages.INTERNAL_SERVER_ERROR,
                    retry_suggested=True
                )
            except:
                pass
        finally:
            # Clean up connection and conversation
            connection_manager.disconnect(client_id)
            await conversation_manager.end_conversation(client_id)
            logger.info(f"Connection cleanup completed for client: {client_id}")
    
    @app.post("/admin/broadcast")
    async def broadcast_message(message: dict):
        """
        Admin endpoint to broadcast messages to all connected clients
        
        Args:
            message: Dictionary containing message content
        """
        if "content" not in message:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        successful_sends = await connection_manager.broadcast(message["content"])
        
        return JSONResponse({
            "status": "success",
            "message": "Broadcast completed",
            "successful_sends": successful_sends,
            "timestamp": datetime.now().isoformat()
        })
    
    @app.get("/admin/connections")
    async def get_connections():
        """Admin endpoint to get information about active connections"""
        active_clients = connection_manager.list_active_clients()
        client_info = {}
        
        for client_id in active_clients:
            client_info[client_id] = connection_manager.get_client_info(client_id)
        
        return JSONResponse({
            "active_connections": connection_manager.get_connection_count(),
            "clients": client_info,
            "timestamp": datetime.now().isoformat()
        })
    
    return app


# Create the FastAPI app instance
app = create_app()

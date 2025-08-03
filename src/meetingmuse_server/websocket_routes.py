"""
WebSocket Routes
FastAPI WebSocket endpoint definitions and health checks
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
from datetime import datetime

from .connection_manager import ConnectionManager
from .message_protocol import MessageProtocol
from .constants import ErrorCodes, ErrorMessages, WebSocketCloseCodes, CloseReasons, SystemMessageTypes

logger = logging.getLogger(__name__)

# Global connection manager instance
connection_manager = ConnectionManager()

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
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": connection_manager.get_connection_count()
        })
    
    @app.get("/health/clients")
    async def detailed_health_check():
        """Detailed health check with connection information"""
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": connection_manager.get_connection_count(),
            "active_clients": connection_manager.list_active_clients(),
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
        
        # Attempt to establish connection
        connection_success = await connection_manager.connect(websocket, client_id)
        if not connection_success:
            await websocket.close(code=WebSocketCloseCodes.INTERNAL_ERROR, reason=CloseReasons.CONNECTION_ESTABLISHMENT_FAILED)
            return
        
        logger.info(f"WebSocket connection established for client: {client_id}")
        
        try:
            while True:
                # Wait for message from client
                message_text = await websocket.receive_text()
                connection_manager.increment_message_count(client_id)
                # TODO: Remove in next iteration
                logger.info(f"Received message from {client_id}: {message_text[:100]}...")
                
                # Parse the incoming message
                user_message = MessageProtocol.parse_user_message(message_text)
                
                if user_message is None:
                    await connection_manager.send_error_message(
                        client_id,
                        ErrorCodes.INVALID_MESSAGE_FORMAT,
                        ErrorMessages.INVALID_MESSAGE_FORMAT,
                        retry_suggested=True
                    )
                    continue
                
                # Send processing notification
                await connection_manager.send_system_message(client_id, SystemMessageTypes.PROCESSING)
                
                # TODO: Simple echo response (placeholder for LangGraph integration)
                response_content = f"Echo: {user_message.content}"
                
                # Send response back to client
                success = await connection_manager.send_personal_message(response_content, client_id)
                
                if not success:
                    logger.warning(f"Failed to send response to client {client_id}")
                    break
                
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
            # Clean up connection
            connection_manager.disconnect(client_id)
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

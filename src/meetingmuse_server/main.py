"""
Main WebSocket Server Application
Entry point for the MeetingMuse WebSocket server
"""
import uvicorn
import logging
from .websocket_routes import app

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the WebSocket server"""
    logger.info("Starting MeetingMuse WebSocket Server...")
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # Enable auto-reload for development # TODO: Use environment variable
        access_log=True
    )
    
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()

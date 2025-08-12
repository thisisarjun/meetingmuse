"""
Main WebSocket Server Application
Entry point for the MeetingMuse WebSocket server
"""
import asyncio
import logging
import signal
import sys

from server.api.app import app, websocket_connection_service
from server.services.server_lifecycle_manager import ServerLifecycleManager

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the WebSocket server"""

    logger.info("Starting MeetingMuse WebSocket Server...")

    server_lifecycle = ServerLifecycleManager(websocket_connection_service)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, server_lifecycle.signal_handler)
    signal.signal(signal.SIGTERM, server_lifecycle.signal_handler)

    try:
        asyncio.run(server_lifecycle.run_server(app))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received during startup")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

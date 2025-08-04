"""
Main WebSocket Server Application
Entry point for the MeetingMuse WebSocket server
"""
import logging
import signal
import sys

from .api.app import app, websocket_connection_service
from .services.graceful_shutdown import GracefulShutdownManager

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the WebSocket server"""
    import asyncio

    logger.info("Starting MeetingMuse WebSocket Server...")

    # Create shutdown manager with dependency injection
    shutdown_manager = GracefulShutdownManager(websocket_connection_service)

    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_manager.signal_handler)
    signal.signal(signal.SIGTERM, shutdown_manager.signal_handler)

    # Handle Windows
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, shutdown_manager.signal_handler)

    try:
        # Run the server
        asyncio.run(shutdown_manager.run_server(app))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received during startup")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

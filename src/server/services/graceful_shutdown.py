"""
Graceful Shutdown Manager
Handles graceful shutdown of the WebSocket server with proper resource cleanup
"""
import asyncio
import logging
from typing import Any, Optional

import uvicorn

from .websocket_connection_handler import WebSocketConnectionService

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manages graceful shutdown of the server and cleanup of resources"""

    def __init__(self, websocket_service: WebSocketConnectionService) -> None:
        self.shutdown_event = asyncio.Event()
        self.server: Optional[uvicorn.Server] = None
        self.websocket_service = websocket_service

    def signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.shutdown_event.set()

    async def cleanup_resources(self) -> None:
        """Clean up WebSocket connections and other resources"""
        logger.info("Cleaning up resources...")

        try:
            # Clean up all connections using the service
            await self.websocket_service.cleanup_all_connections()

            logger.info("Resource cleanup completed")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {str(e)}")

    async def run_server(
        self, app: Any, host: str = "0.0.0.0", port: int = 8000
    ) -> None:
        """Run the server with graceful shutdown handling"""
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            reload=False,  # Disable reload for proper signal handling
            access_log=True,
        )

        self.server = uvicorn.Server(config)
        server_task = None

        try:
            # Start the server in a task
            server_task = asyncio.create_task(self.server.serve())

            # Create a task to wait for shutdown signal
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())

            # Wait for either server completion or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if shutdown was requested
            if shutdown_task in done:
                logger.info("Shutdown signal received, stopping server...")

                # Stop accepting new connections
                if self.server:
                    self.server.should_exit = True

                # Clean up resources
                await self.cleanup_resources()

                # Wait for server to finish with timeout
                if server_task and not server_task.done():
                    try:
                        await asyncio.wait_for(server_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning("Server shutdown timed out, cancelling task")
                        server_task.cancel()
                        try:
                            await server_task
                        except asyncio.CancelledError:
                            pass
            else:
                # Server task completed (likely with error)
                if server_task in done:
                    try:
                        await server_task  # This will raise the exception if any
                    except Exception as e:
                        logger.error(f"Server task failed: {str(e)}")
                        raise

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
            if self.server:
                self.server.should_exit = True
            await self.cleanup_resources()
        except Exception as e:
            logger.error(f"Error during server operation: {str(e)}")
            raise
        finally:
            # Ensure server task is cancelled if still running
            if server_task and not server_task.done():
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass
            logger.info("Server shutdown complete")

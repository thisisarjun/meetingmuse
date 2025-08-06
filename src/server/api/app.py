"""
FastAPI Application Factory
Creates and configures the main FastAPI application with all routes and services
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from ..langgraph.message_processor import LangGraphMessageProcessor
from ..langgraph.streaming_handler import StreamingHandler
from ..services.admin_service import AdminService
from ..services.connection_manager import ConnectionManager
from ..services.conversation_manager import ConversationManager
from ..services.health_service import HealthService
from ..services.websocket_connection_service import WebSocketConnectionService
from .admin_api import create_admin_router
from .health_api import create_health_router
from .websocket_api import create_websocket_router

logger = logging.getLogger(__name__)

# Global service instances - initialized once
connection_manager = ConnectionManager()
conversation_manager = ConversationManager()
message_processor = LangGraphMessageProcessor()
streaming_handler = StreamingHandler()

# Create specialized services with dependency injection
health_service = HealthService(
    connection_manager=connection_manager,
    conversation_manager=conversation_manager,
    message_processor=message_processor,
    streaming_handler=streaming_handler,
)

admin_service = AdminService(
    connection_manager=connection_manager,
    conversation_manager=conversation_manager,
)

websocket_connection_service = WebSocketConnectionService(
    connection_manager=connection_manager,
    conversation_manager=conversation_manager,
    message_processor=message_processor,
    streaming_handler=streaming_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("MeetingMuse WebSocket Server starting up...")
    logger.info(
        f"Connection manager initialized: {connection_manager.get_connection_count()} connections"
    )

    yield

    # Shutdown
    logger.info("MeetingMuse WebSocket Server shutting down...")

    # Clean up all connections using the service
    await websocket_connection_service.cleanup_all_connections()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="MeetingMuse WebSocket Server",
        description="WebSocket server for MeetingMuse chat application with modular architecture",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Include API routers
    app.include_router(create_health_router(health_service))
    app.include_router(create_admin_router(admin_service))
    app.include_router(create_websocket_router(websocket_connection_service))

    logger.info("FastAPI server initialized with routers")
    return app


app = create_app()

__all__ = [
    "app",
    "connection_manager",
    "conversation_manager",
    "health_service",
    "admin_service",
    "websocket_connection_service",
]

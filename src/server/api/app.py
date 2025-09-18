"""
FastAPI Application Factory
Creates and configures the main FastAPI application with all routes and services
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config.config import config
from common.logger import Logger

from ..dependency_container import DependencyContainer
from .auth_api import create_auth_router
from .health_api import create_health_router
from .websocket_api import create_websocket_router

logger = Logger()

# Initialize dependency container based on environment
if config.ENV == "dev":
    container = DependencyContainer.create_development()
else:
    container = DependencyContainer.create_production()

# Global service instances accessed through container
connection_manager = container.connection_manager
conversation_manager = container.conversation_manager
health_service = container.health_service
websocket_connection_service = container.websocket_connection_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("MeetingMuse WebSocket Server starting up...")
    logger.info("Connection manager initialized")

    yield

    # Shutdown
    logger.info("MeetingMuse WebSocket Server shutting down...")

    websocket_connection_service.cleanup_all_connections()
    # Clean up all connections using the service

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="MeetingMuse WebSocket Server",
        description="""
        ## MeetingMuse WebSocket Server API

        WebSocket server for real-time chat communication powered by LangGraph.

        ### API Endpoints

        * **WebSocket**: Real-time communication endpoints
        * **Authentication**: OAuth flow for user authentication

        ### Authentication

        TODO
        Implement authentication for WebSocket connections and API endpoints.
        """,
        version="2.0.0",
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        tags_metadata=[
            {
                "name": "websocket",
                "description": "WebSocket endpoints for real-time chat communication. Clients connect here to send and receive messages through the LangGraph-powered chat system.",
            },
            {
                "name": "authentication",
                "description": "OAuth flow for user authentication.",
            },
        ],
        lifespan=lifespan,
    )

    if config.ENV == "dev":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://meetingmuse.vercel.app"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Include API routers
    app.include_router(create_websocket_router(websocket_connection_service, logger))
    app.include_router(create_auth_router())
    app.include_router(create_health_router(health_service, logger))

    logger.info("FastAPI server initialized with routers")
    return app


app = create_app()

__all__ = [
    "app",
    "connection_manager",
    "conversation_manager",
    "websocket_connection_service",
]

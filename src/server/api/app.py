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
from meetingmuse.clients.google_calendar import GoogleCalendarClient
from meetingmuse.graph.graph import GraphBuilder
from meetingmuse.graph.graph_message_processor import GraphMessageProcessor
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.end_node import EndNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode
from meetingmuse.nodes.human_schedule_meeting_more_info_node import (
    HumanScheduleMeetingMoreInfoNode,
)
from meetingmuse.nodes.prompt_missing_meeting_details_node import (
    PromptMissingMeetingDetailsNode,
)
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.routing_service import ConversationRouter

from ..services.connection_manager import ConnectionManager
from ..services.conversation_manager import ConversationManager
from ..services.health_service import HealthService
from ..services.websocket_connection_service import WebSocketConnectionService
from .auth_api import create_auth_router
from .dependencies import get_oauth_service
from .health_api import create_health_router
from .websocket_api import create_websocket_router

logger = Logger()

# Node creation and graph creation
# TODO: move to separate method
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier, logger)
greeting_node = GreetingNode(model, logger)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model, logger)
meeting_details_service = MeetingDetailsService(model, logger)
human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger)
prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
    meeting_details_service, logger
)
google_calendar_client = GoogleCalendarClient(get_oauth_service(), logger)
schedule_meeting_node = ScheduleMeetingNode(model, logger, google_calendar_client)
human_interrupt_retry_node = HumanInterruptRetryNode(logger)
end_node = EndNode(logger)
conversation_router = ConversationRouter(logger)

graph = GraphBuilder(
    state=MeetingMuseBotState,
    greeting_node=greeting_node,
    clarify_request_node=clarify_request_node,
    collecting_info_node=collecting_info_node,
    schedule_meeting_node=schedule_meeting_node,
    human_interrupt_retry_node=human_interrupt_retry_node,
    conversation_router=conversation_router,
    classify_intent_node=classify_intent_node,
    human_schedule_meeting_more_info_node=human_schedule_meeting_more_info_node,
    prompt_missing_meeting_details_node=prompt_missing_meeting_details_node,
    end_node=end_node,
).build()
message_processor = GraphMessageProcessor(graph=graph, logger=logger)

# Global service instances - initialized once
connection_manager = ConnectionManager()
conversation_manager = ConversationManager(
    logger=logger, message_processor=message_processor
)

# Create specialized services with dependency injection

health_service = HealthService(connection_manager=connection_manager)
websocket_connection_service = WebSocketConnectionService(
    connection_manager=connection_manager,
    conversation_manager=conversation_manager,
    message_processor=message_processor,
    logger=logger,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("MeetingMuse WebSocket Server starting up...")
    logger.info("Connection manager initialized")

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

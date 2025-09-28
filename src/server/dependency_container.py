from dataclasses import dataclass
from typing import Literal, Optional

from langgraph.graph.state import CompiledStateGraph
from redis.asyncio import Redis

from common.config.config import config
from common.logger import Logger
from meetingmuse.clients.google_calendar import GoogleCalendarClient
from meetingmuse.clients.google_contacts import GoogleContactsClient
from meetingmuse.graph.graph import GraphBuilder
from meetingmuse.graph.graph_message_processor import GraphMessageProcessor
from meetingmuse.llm_models.base import BaseLlmModel
from meetingmuse.llm_models.factory import create_llm_model
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
from meetingmuse.prompts.reminder_collecting_info_prompt import (
    REMINDER_COLLECTING_INFO_PROMPT,
)
from meetingmuse.prompts.schedule_meeting_collecting_info_prompt import (
    INTERACTIVE_MEETING_COLLECTION_PROMPT,
)
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.reminder_details_service import ReminderDetailsService
from meetingmuse.services.routing_service import ConversationRouter
from server.services.connection_manager import ConnectionManager
from server.services.conversation_manager import ConversationManager
from server.services.health_service import HealthService
from server.services.oauth_service import OAuthService
from server.services.session_manager import SessionManager
from server.services.websocket_connection_service import WebSocketConnectionService
from server.storage.memory_storage import MemoryStorageAdapter
from server.storage.redis_adapter import RedisStorageAdapter
from server.storage.storage_adapter import StorageAdapter


@dataclass
class DependencyConfig:
    """Configuration for dependency container"""

    model_name: str
    provider: str
    storage_type: Literal["memory", "redis"] = "memory"
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None


class DependencyContainer:
    """Centralized dependency injection container for MeetingMuse application"""

    def __init__(self, config: Optional[DependencyConfig] = None) -> None:
        """Initialize dependency container with configuration

        Args:
            config: Dependency configuration. If None, uses default config.
        """
        self._config = config or DependencyConfig(
            model_name="gpt-4o-mini", provider="openai", storage_type="memory"
        )

        # Initialize all dependencies as None - will be lazily loaded
        self._logger: Optional[Logger] = None

        # LLM dependencies
        self._model: Optional[BaseLlmModel] = None

        # Storage dependencies
        self._storage_adapter: Optional[StorageAdapter] = None
        self._session_manager: Optional[SessionManager] = None

        # OAuth dependencies
        self._oauth_service: Optional[OAuthService] = None

        # Graph dependencies
        self._intent_classifier: Optional[IntentClassifier] = None
        self._classify_intent_node: Optional[ClassifyIntentNode] = None
        self._greeting_node: Optional[GreetingNode] = None
        self._collecting_info_node: Optional[CollectingInfoNode] = None
        self._clarify_request_node: Optional[ClarifyRequestNode] = None
        self._meeting_details_service: Optional[MeetingDetailsService] = None
        self._reminder_details_service: Optional[ReminderDetailsService] = None
        self._human_schedule_meeting_more_info_node: Optional[
            HumanScheduleMeetingMoreInfoNode
        ] = None
        self._prompt_missing_meeting_details_node: Optional[
            PromptMissingMeetingDetailsNode
        ] = None
        self._schedule_meeting_node: Optional[ScheduleMeetingNode] = None
        self._human_interrupt_retry_node: Optional[HumanInterruptRetryNode] = None
        self._end_node: Optional[EndNode] = None
        self._conversation_router: Optional[ConversationRouter] = None
        self._graph: Optional[CompiledStateGraph] = None
        self._graph_message_processor: Optional[GraphMessageProcessor] = None

        # External dependencies
        self._google_calendar_client: Optional[GoogleCalendarClient] = None
        self._google_contacts_client: Optional[GoogleContactsClient] = None

        # API and WebSocket dependencies
        self._connection_manager: Optional[ConnectionManager] = None
        self._conversation_manager: Optional[ConversationManager] = None
        self._health_service: Optional[HealthService] = None
        self._websocket_connection_service: Optional[WebSocketConnectionService] = None

    def _validate_config(self) -> None:
        """Validate dependency configuration"""
        if self._config.storage_type == "redis":
            redis_host = self._config.redis_host or config.REDIS_HOST
            redis_port = self._config.redis_port or config.REDIS_PORT
            if not redis_host or not redis_port:
                raise ValueError(
                    "Redis configuration incomplete. Set REDIS_HOST and REDIS_PORT."
                )

        if not self._config.model_name or not self._config.provider:
            raise ValueError(
                "LLM configuration incomplete. model_name and provider are required."
            )

    @classmethod
    def create_development(cls) -> "DependencyContainer":
        """Create container for development environment"""
        return cls(
            DependencyConfig(
                model_name="gpt-4o-mini",
                provider="openai",
                storage_type="redis",
                redis_host=config.REDIS_HOST,
                redis_port=config.REDIS_PORT,
            )
        )

    @classmethod
    def create_production(cls) -> "DependencyContainer":
        """Create container for production environment"""
        return cls(
            DependencyConfig(
                model_name="gpt-4o",
                provider="openai",
                storage_type="redis",
                redis_host=config.REDIS_HOST,
                redis_port=config.REDIS_PORT,
            )
        )

    # Lazy-loaded properties for dependency injection

    @property
    def logger(self) -> Logger:
        """Get logger instance"""
        if self._logger is None:
            self._logger = Logger()
        return self._logger

    @property
    def model(self) -> BaseLlmModel:
        """Get LLM model instance"""
        if self._model is not None:
            return self._model
        try:
            self._validate_config()
            self._model = create_llm_model(
                self._config.model_name, self._config.provider
            )
            return self._model
        except Exception as e:
            self.logger.error(f"Failed to create LLM model: {e}")
            raise RuntimeError(f"Failed to create LLM model: {e}")

    @property
    def storage_adapter(self) -> StorageAdapter:
        """Get storage adapter instance"""
        if self._storage_adapter is not None:
            return self._storage_adapter

        try:
            if self._config.storage_type == "redis":
                redis_host = self._config.redis_host or config.REDIS_HOST
                redis_port = self._config.redis_port or config.REDIS_PORT
                redis_client = Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True,
                )
                self._storage_adapter = RedisStorageAdapter(redis_client)
                return self._storage_adapter
            elif self._config.storage_type == "memory":
                self._storage_adapter = MemoryStorageAdapter()
                return self._storage_adapter
            else:
                raise ValueError(
                    f"Invalid storage adapter type: {self._config.storage_type}"
                )
        except Exception as e:
            self.logger.error(f"Failed to create storage adapter: {e}")
            raise RuntimeError(f"Failed to create storage adapter: {e}")

    @property
    def session_manager(self) -> SessionManager:
        """Get session manager instance"""
        if self._session_manager is not None:
            return self._session_manager
        try:
            self._session_manager = SessionManager(self.storage_adapter, self.logger)
            return self._session_manager
        except Exception as e:
            self.logger.error(f"Failed to create session manager: {e}")
            raise RuntimeError(f"Failed to create session manager: {e}")

    @property
    def oauth_service(self) -> OAuthService:
        """Get OAuth service instance"""
        if self._oauth_service is not None:
            return self._oauth_service
        try:
            self._oauth_service = OAuthService(self.session_manager, self.logger)
            return self._oauth_service
        except Exception as e:
            self.logger.error(f"Failed to create OAuth service: {e}")
            raise RuntimeError(f"Failed to create OAuth service: {e}")

    @property
    def google_calendar_client(self) -> GoogleCalendarClient:
        """Get Google Calendar client instance"""
        if self._google_calendar_client is not None:
            return self._google_calendar_client

        try:
            self._google_calendar_client = GoogleCalendarClient(
                self.oauth_service, self.logger
            )
            return self._google_calendar_client
        except Exception as e:
            self.logger.error(f"Failed to create Google Calendar client: {e}")
            raise RuntimeError(f"Failed to create Google Calendar client: {e}")

    @property
    def google_contacts_client(self) -> GoogleContactsClient:
        """Get Google Contacts client instance"""
        if self._google_contacts_client is not None:
            return self._google_contacts_client

        try:
            self._google_contacts_client = GoogleContactsClient(
                self.oauth_service, self.logger
            )
            return self._google_contacts_client
        except Exception as e:
            self.logger.error(f"Failed to create Google Contacts client: {e}")
            raise RuntimeError(f"Failed to create Google Contacts client: {e}")

    @property
    def intent_classifier(self) -> IntentClassifier:
        """Get intent classifier instance"""
        if self._intent_classifier is not None:
            return self._intent_classifier

        try:
            self._intent_classifier = IntentClassifier(self.model)
            return self._intent_classifier
        except Exception as e:
            self.logger.error(f"Failed to create intent classifier: {e}")
            raise RuntimeError(f"Failed to create intent classifier: {e}")

    @property
    def classify_intent_node(self) -> ClassifyIntentNode:
        """Get classify intent node instance"""
        if self._classify_intent_node is not None:
            return self._classify_intent_node

        try:
            self._classify_intent_node = ClassifyIntentNode(
                self.intent_classifier, self.logger
            )
            return self._classify_intent_node
        except Exception as e:
            self.logger.error(f"Failed to create classify intent node: {e}")
            raise RuntimeError(f"Failed to create classify intent node: {e}")

    @property
    def greeting_node(self) -> GreetingNode:
        """Get greeting node instance"""
        if self._greeting_node is not None:
            return self._greeting_node

        try:
            self._greeting_node = GreetingNode(self.model, self.logger)
            return self._greeting_node
        except Exception as e:
            self.logger.error(f"Failed to create greeting node: {e}")
            raise RuntimeError(f"Failed to create greeting node: {e}")

    @property
    def collecting_info_node(self) -> CollectingInfoNode:
        """Get collecting info node instance"""
        if self._collecting_info_node is not None:
            return self._collecting_info_node

        try:
            self._collecting_info_node = CollectingInfoNode(
                self.model,
                self.logger,
                self.meeting_details_service,
                self.reminder_details_service,
            )
            return self._collecting_info_node
        except Exception as e:
            self.logger.error(f"Failed to create collecting info node: {e}")
            raise RuntimeError(f"Failed to create collecting info node: {e}")

    @property
    def clarify_request_node(self) -> ClarifyRequestNode:
        """Get clarify request node instance"""
        if self._clarify_request_node is not None:
            return self._clarify_request_node

        try:
            self._clarify_request_node = ClarifyRequestNode(self.model, self.logger)
            return self._clarify_request_node
        except Exception as e:
            self.logger.error(f"Failed to create clarify request node: {e}")
            raise RuntimeError(f"Failed to create clarify request node: {e}")

    @property
    def meeting_details_service(self) -> MeetingDetailsService:
        """Get meeting details service instance"""
        if self._meeting_details_service is not None:
            return self._meeting_details_service

        try:
            self._meeting_details_service = MeetingDetailsService(
                self.model, self.logger, INTERACTIVE_MEETING_COLLECTION_PROMPT
            )
            return self._meeting_details_service
        except Exception as e:
            self.logger.error(f"Failed to create meeting details service: {e}")
            raise RuntimeError(f"Failed to create meeting details service: {e}")

    @property
    def reminder_details_service(self) -> ReminderDetailsService:
        """Get reminder details service instance"""
        if self._reminder_details_service is not None:
            return self._reminder_details_service
        try:
            self._reminder_details_service = ReminderDetailsService(
                self.model, self.logger, REMINDER_COLLECTING_INFO_PROMPT
            )
            return self._reminder_details_service
        except Exception as e:
            self.logger.error(f"Failed to create reminder details service: {e}")
            raise RuntimeError(f"Failed to create reminder details service: {e}")

    @property
    def human_schedule_meeting_more_info_node(self) -> HumanScheduleMeetingMoreInfoNode:
        """Get human schedule meeting more info node instance"""
        if self._human_schedule_meeting_more_info_node is not None:
            return self._human_schedule_meeting_more_info_node

        try:
            self._human_schedule_meeting_more_info_node = (
                HumanScheduleMeetingMoreInfoNode(self.logger)
            )
            return self._human_schedule_meeting_more_info_node
        except Exception as e:
            self.logger.error(
                f"Failed to create human schedule meeting more info node: {e}"
            )
            raise RuntimeError(
                f"Failed to create human schedule meeting more info node: {e}"
            )

    @property
    def prompt_missing_meeting_details_node(self) -> PromptMissingMeetingDetailsNode:
        """Get prompt missing meeting details node instance"""
        if self._prompt_missing_meeting_details_node is not None:
            return self._prompt_missing_meeting_details_node

        try:
            self._prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
                self.meeting_details_service, self.reminder_details_service, self.logger
            )
            return self._prompt_missing_meeting_details_node
        except Exception as e:
            self.logger.error(
                f"Failed to create prompt missing meeting details node: {e}"
            )
            raise RuntimeError(
                f"Failed to create prompt missing meeting details node: {e}"
            )

    @property
    def schedule_meeting_node(self) -> ScheduleMeetingNode:
        """Get schedule meeting node instance"""
        if self._schedule_meeting_node is not None:
            return self._schedule_meeting_node

        try:
            self._schedule_meeting_node = ScheduleMeetingNode(
                self.model, self.logger, self.google_calendar_client
            )
            return self._schedule_meeting_node
        except Exception as e:
            self.logger.error(f"Failed to create schedule meeting node: {e}")
            raise RuntimeError(f"Failed to create schedule meeting node: {e}")

    @property
    def human_interrupt_retry_node(self) -> HumanInterruptRetryNode:
        """Get human interrupt retry node instance"""
        if self._human_interrupt_retry_node is not None:
            return self._human_interrupt_retry_node

        try:
            self._human_interrupt_retry_node = HumanInterruptRetryNode(self.logger)
            return self._human_interrupt_retry_node
        except Exception as e:
            self.logger.error(f"Failed to create human interrupt retry node: {e}")
            raise RuntimeError(f"Failed to create human interrupt retry node: {e}")

    @property
    def end_node(self) -> EndNode:
        """Get end node instance"""
        if self._end_node is not None:
            return self._end_node

        try:
            self._end_node = EndNode(self.logger)
            return self._end_node
        except Exception as e:
            self.logger.error(f"Failed to create end node: {e}")
            raise RuntimeError(f"Failed to create end node: {e}")

    @property
    def conversation_router(self) -> ConversationRouter:
        """Get conversation router instance"""
        if self._conversation_router is not None:
            return self._conversation_router

        try:
            self._conversation_router = ConversationRouter(self.logger)
            return self._conversation_router
        except Exception as e:
            self.logger.error(f"Failed to create conversation router: {e}")
            raise RuntimeError(f"Failed to create conversation router: {e}")

    @property
    def graph(self) -> CompiledStateGraph:
        """Get compiled graph instance"""
        if self._graph is not None:
            return self._graph

        try:
            self._graph = GraphBuilder(
                state=MeetingMuseBotState,
                greeting_node=self.greeting_node,
                clarify_request_node=self.clarify_request_node,
                collecting_info_node=self.collecting_info_node,
                schedule_meeting_node=self.schedule_meeting_node,
                human_interrupt_retry_node=self.human_interrupt_retry_node,
                conversation_router=self.conversation_router,
                classify_intent_node=self.classify_intent_node,
                human_schedule_meeting_more_info_node=self.human_schedule_meeting_more_info_node,
                prompt_missing_meeting_details_node=self.prompt_missing_meeting_details_node,
                end_node=self.end_node,
            ).build()
            return self._graph
        except Exception as e:
            self.logger.error(f"Failed to create graph: {e}")
            raise RuntimeError(f"Failed to create graph: {e}")

    @property
    def graph_message_processor(self) -> GraphMessageProcessor:
        """Get graph message processor instance"""
        if self._graph_message_processor is not None:
            return self._graph_message_processor

        try:
            self._graph_message_processor = GraphMessageProcessor(
                graph=self.graph, logger=self.logger
            )
            return self._graph_message_processor
        except Exception as e:
            self.logger.error(f"Failed to create graph message processor: {e}")
            raise RuntimeError(f"Failed to create graph message processor: {e}")

    @property
    def connection_manager(self) -> ConnectionManager:
        """Get connection manager instance"""
        if self._connection_manager is not None:
            return self._connection_manager

        try:
            self._connection_manager = ConnectionManager()
            return self._connection_manager
        except Exception as e:
            self.logger.error(f"Failed to create connection manager: {e}")
            raise RuntimeError(f"Failed to create connection manager: {e}")

    @property
    def conversation_manager(self) -> ConversationManager:
        """Get conversation manager instance"""
        if self._conversation_manager is not None:
            return self._conversation_manager

        try:
            self._conversation_manager = ConversationManager(
                logger=self.logger, graph_message_processor=self.graph_message_processor
            )
            return self._conversation_manager
        except Exception as e:
            self.logger.error(f"Failed to create conversation manager: {e}")
            raise RuntimeError(f"Failed to create conversation manager: {e}")

    @property
    def health_service(self) -> HealthService:
        """Get health service instance"""
        if self._health_service is not None:
            return self._health_service

        try:
            self._health_service = HealthService(
                connection_manager=self.connection_manager
            )
            return self._health_service
        except Exception as e:
            self.logger.error(f"Failed to create health service: {e}")
            raise RuntimeError(f"Failed to create health service: {e}")

    @property
    def websocket_connection_service(self) -> WebSocketConnectionService:
        """Get websocket connection service instance"""
        if self._websocket_connection_service is not None:
            return self._websocket_connection_service

        try:
            self._websocket_connection_service = WebSocketConnectionService(
                connection_manager=self.connection_manager,
                conversation_manager=self.conversation_manager,
                graph_message_processor=self.graph_message_processor,
                logger=self.logger,
            )
            return self._websocket_connection_service
        except Exception as e:
            self.logger.error(f"Failed to create websocket connection service: {e}")
            raise RuntimeError(f"Failed to create websocket connection service: {e}")

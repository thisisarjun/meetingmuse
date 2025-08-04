"""
LangGraph Factory for WebSocket Server
Creates and configures LangGraph instances for conversation processing
"""
from typing import Any, Optional
import logging
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from meetingmuse.graph import GraphBuilder
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode
from meetingmuse.nodes.human_schedule_meeting_more_info_node import HumanScheduleMeetingMoreInfoNode
from meetingmuse.nodes.prompt_missing_meeting_details_node import PromptMissingMeetingDetailsNode
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode  
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger

logger = logging.getLogger(__name__)


class LangGraphSingletonFactory:
    """Singleton factory class for creating and configuring LangGraph instances"""
    
    _instance = None
    _lock = None
    
    def __new__(cls):
        """Ensure only one instance exists (thread-safe singleton)"""
        if cls._instance is None:
            import threading
            if cls._lock is None:
                cls._lock = threading.Lock()
            
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LangGraphSingletonFactory, cls).__new__(cls)
                    cls._instance._graph_instance = None
                    cls._instance._model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
                    cls._instance._initialized = False
        
        return cls._instance
    
    def __init__(self):
        """Private constructor - prevents direct instantiation"""
        # Prevent re-initialization of already created instance
        if hasattr(self, '_initialized'):
            return
    
    @classmethod
    def get_instance(cls) -> 'LangGraphSingletonFactory':
        """
        Get the singleton instance of the factory.
        This is the only public way to obtain the factory instance.
        
        Returns:
            The singleton LangGraphSingletonFactory instance
        """
        return cls()
    
    @classmethod 
    def get_graph(cls) -> Any:
        """
        Public interface to get the LangGraph instance.
        This ensures the graph is created only once across the entire application.
        
        Returns:
            Compiled LangGraph conversation graph
        """
        instance = cls.get_instance()
        return instance.get_graph_instance()
    
    @staticmethod
    def _create_conversation_graph() -> Any:
        """
        Initialize and return configured LangGraph instance (private method)
        
        Returns:
            Compiled LangGraph conversation graph
        """
        try:
            meetingmuse_logger = Logger()
            
            # Initialize LLM model
            model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
            
            # Initialize services
            intent_classifier = IntentClassifier(model)
            conversation_router = ConversationRouter(meetingmuse_logger)
            meeting_details_service = MeetingDetailsService(model, meetingmuse_logger)
            
            # Initialize nodes
            classify_intent_node = ClassifyIntentNode(intent_classifier)
            greeting_node = GreetingNode(model)
            clarify_request_node = ClarifyRequestNode(model) 
            collecting_info_node = CollectingInfoNode(model, meetingmuse_logger)
            schedule_meeting_node = ScheduleMeetingNode(model, meetingmuse_logger)
            human_interrupt_retry_node = HumanInterruptRetryNode(meetingmuse_logger)
            human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(meetingmuse_logger)
            prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
                meetingmuse_logger, meeting_details_service
            )
            
            # Create graph builder with all components
            graph_builder = GraphBuilder(
                state=MeetingMuseBotState,
                greeting_node=greeting_node,
                clarify_request_node=clarify_request_node,
                collecting_info_node=collecting_info_node,
                classify_intent_node=classify_intent_node,
                schedule_meeting_node=schedule_meeting_node,
                human_interrupt_retry_node=human_interrupt_retry_node,
                conversation_router=conversation_router,
                human_schedule_meeting_more_info_node=human_schedule_meeting_more_info_node,
                prompt_missing_meeting_details_node=prompt_missing_meeting_details_node,
            )
            
            # Build and return the compiled graph
            graph = graph_builder.build()
            
            logger.info("LangGraph conversation graph created successfully")
            return graph
            
        except Exception as e:
            logger.error(f"Failed to create LangGraph conversation graph: {str(e)}")
            raise e
    
    def get_graph_instance(self) -> Any:
        """
        Get the singleton instance of the conversation graph.
        Creates the graph only once and reuses it for all subsequent calls.
        
        Returns:
            Compiled LangGraph conversation graph
        """
        if not self._graph_instance:
            logger.info("Creating new LangGraph instance (first time initialization)")
            self._graph_instance = self._create_conversation_graph()
            self._initialized = True
        else:
            logger.debug("Returning existing LangGraph instance (singleton)")
        
        return self._graph_instance
    
    def is_initialized(self) -> bool:
        """Check if the graph factory is initialized"""
        return self._initialized
    
    def reset(self) -> None:
        """Reset the factory instance (useful for testing)"""
        self._graph_instance = None
        self._initialized = False

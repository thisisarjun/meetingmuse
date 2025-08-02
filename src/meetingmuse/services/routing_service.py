from typing import Optional
from meetingmuse.models.node import NodeName
from meetingmuse.utils import Logger
from meetingmuse.models.state import MeetingMuseBotState, UserIntent


class ConversationRouter:
    """
    Handles global conversation routing based on user intent and cross-node decisions.
    
    This router is responsible for:
    - Intent-based routing between different conversation flows
    - Cross-node routing decisions that affect multiple nodes
    - Global conversation state transitions
    
    For node-specific routing (e.g., completion checks, internal loops), 
    implement routing logic directly in the node class rather than here.
    """
    
    logger: Logger
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        
    def intent_to_node_name_router(self, state: MeetingMuseBotState) -> NodeName:
        intent: Optional[UserIntent] = state.user_intent
        next_step: NodeName = NodeName.GREETING
        if intent == UserIntent.GENERAL_CHAT:
            next_step = NodeName.GREETING
        if intent == UserIntent.SCHEDULE_MEETING:
            next_step = NodeName.COLLECTING_INFO
        if intent == UserIntent.UNKNOWN or intent is None:
            next_step = NodeName.CLARIFY_REQUEST
        
        self.logger.info(f"Routing to {next_step}")
        return next_step


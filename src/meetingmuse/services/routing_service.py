from meetingmuse.models.node import NodeName
from meetingmuse.utils import Logger
from meetingmuse.models.state import MeetingMuseBotState, ConversationStep, UserIntent

class ConversationRouter:    
    
    def __init__(self, logger: Logger):
        self.logger = logger
    def route(self, state: MeetingMuseBotState) -> NodeName:
        intent = state.user_intent
        next_step = NodeName.GREETING
        if intent == UserIntent.GENERAL_CHAT:
            next_step = NodeName.GREETING
        if intent == UserIntent.SCHEDULE_MEETING:
            next_step = NodeName.SCHEDULE_MEETING
        if intent == UserIntent.UNKNOWN:
            next_step = NodeName.CLARIFY_REQUEST
        
        self.logger.info(f"Routing to {next_step}")
        return next_step


    

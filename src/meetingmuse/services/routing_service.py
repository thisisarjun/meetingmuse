from meetingmuse.models.node import NodeName
from meetingmuse.utils import Logger
from meetingmuse.models.state import CalendarBotState, ConversationStep

class ConversationRouter:    
    
    def __init__(self, logger: Logger):
        self.logger = logger
# FIXME: return node_name instead of value
    def route(self, state: CalendarBotState) -> NodeName:
        current_step = state["current_step"]
        next_step = NodeName.GREETING
        if current_step == ConversationStep.GREETING:
            next_step = NodeName.GREETING
        if current_step == ConversationStep.COLLECTING_INFO:
            next_step = NodeName.SCHEDULE_MEETING
        if current_step == ConversationStep.PROCESSING_REQUEST:
            next_step = NodeName.PROCESS_REQUEST
        if current_step == ConversationStep.COMPLETED:
            next_step = NodeName.PROCESS_REQUEST
        if current_step == ConversationStep.CLARIFYING_REQUEST:
            next_step = NodeName.CLARIFY_REQUEST
        
        self.logger.info(f"Routing to {next_step}")
        return next_step


    

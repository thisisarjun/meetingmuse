from meetingmuse.utils import Logger
from meetingmuse.models.state import CalendarBotState, ConversationStep

class ConversationRouter:    
    
    def __init__(self, logger: Logger):
        self.logger = logger

    def route(self, state: CalendarBotState) -> ConversationStep:
        current_step = state["current_step"]
        next_step = ConversationStep.GREETING
        if current_step == ConversationStep.GREETING:
            next_step = ConversationStep.GREETING
        if current_step == ConversationStep.COLLECTING_INFO:
            next_step = ConversationStep.COLLECTING_INFO
        if current_step == ConversationStep.PROCESSING_REQUEST:
            next_step = ConversationStep.PROCESSING_REQUEST
        if current_step == ConversationStep.COMPLETED:
            next_step = ConversationStep.COMPLETED
        if current_step == ConversationStep.CLARIFYING_REQUEST:
            next_step = ConversationStep.CLARIFYING_REQUEST    
        
        self.logger.info(f"Routing to {next_step}")
        return next_step


    

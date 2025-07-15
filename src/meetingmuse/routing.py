from meetingmuse.models.state import CalendarBotState, ConversationStep

def route_coversation(state: CalendarBotState) -> str:
    
    current_step = state["current_step"]
    if current_step == ConversationStep.GREETING:
        return "greeting"
    if current_step == ConversationStep.COLLECTING_INFO:
        return "schedule_meeting"
    if current_step == ConversationStep.PROCESSING_REQUEST:
        return "process_request"
    if current_step == ConversationStep.COMPLETED:
        return "completed"
    if current_step == ConversationStep.CLARIFYING_REQUEST:
        return "clarify_request"    
    return ConversationStep.GREETING

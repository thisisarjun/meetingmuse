from enum import StrEnum
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class UserIntent(StrEnum):
    SCHEDULE_MEETING = "schedule"
    CHECK_AVAILABILITY = "check_availability"
    CANCEL_MEETING = "cancel"
    RESCHEDULE_MEETING = "reschedule"
    GENERAL_CHAT = "general"
    UNKNOWN = "unknown"

class ConversationStep(StrEnum):
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    PROCESSING_REQUEST = "processing"
    CLARIFYING_REQUEST = "clarifying"
    COMPLETED = "completed"


# TODO: Make this a pydantic model
class MeetingMuseBotState(TypedDict):
    """
    This is the 'memory' of your bot - everything it remembers during a conversation.
    
    Think of this as the bot's notebook where it writes down:
    - What the user said
    - What it figured out about the user's intent
    - Where it is in the conversation process
    - Details about the meeting being planned
    """
    
    # The conversation history (user + bot messages)
    messages: Annotated[List, add_messages]
    
    # What does the user want? (schedule, cancel, check availability, etc.)
    user_intent: Optional[UserIntent] 
    
    # Where are we in the conversation? (greeting, collecting info, confirming, etc.)
    current_step: ConversationStep
    
    # Information about the meeting being scheduled
    meeting_details: Dict[str, Any]
from enum import StrEnum
from typing import Any, Dict, List, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from meetingmuse.models.meeting import MeetingFindings


class UserIntent(StrEnum):
    SCHEDULE_MEETING = "schedule"
    CHECK_AVAILABILITY = "check_availability"
    CANCEL_MEETING = "cancel"
    RESCHEDULE_MEETING = "reschedule"
    GENERAL_CHAT = "general"
    UNKNOWN = "unknown"


class MeetingMuseBotState(BaseModel):
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
    user_intent: Optional[UserIntent] = None
    
    # Information about the meeting being scheduled
    meeting_details: MeetingFindings = Field(default_factory=MeetingFindings)
    
    # API call status for retry logic
    api_call_status: Optional[str] = None
    api_error_message: Optional[str] = None

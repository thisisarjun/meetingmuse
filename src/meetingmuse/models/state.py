from enum import StrEnum
from typing import List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from meetingmuse.models.meeting import MeetingFindings


class UserIntent(StrEnum):
    GENERAL_CHAT = "general"
    SCHEDULE_MEETING = "schedule"
    REMINDER = "reminder"
    UNKNOWN = "unknown"


class OperationStatus(BaseModel):
    status: bool = False
    error_message: Optional[str] = None
    ai_prompt_input: Optional[str] = None


class UserDetails(BaseModel):
    session_id: Optional[str] = None
    timezone: Optional[str] = None


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
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    # What does the user want? (schedule, cancel, check availability, etc.)
    user_intent: Optional[UserIntent] = None

    # Information about the meeting being scheduled (also used for reminders)
    meeting_details: MeetingFindings = Field(default_factory=MeetingFindings)

    operation_status: OperationStatus = Field(default_factory=OperationStatus)

    user_details: Optional[UserDetails] = Field(default_factory=UserDetails)

from enum import StrEnum
from typing import List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from meetingmuse.models.meeting import MeetingFindings


class UserIntent(StrEnum):
    GENERAL_CHAT = "general_chat"
    SCHEDULE_MEETING = "schedule_meeting"
    CANCEL_MEETING = "cancel_meeting"
    CHECK_AVAILABILITY = "check_availability"
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
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)

    # What does the user want? (schedule, cancel, check availability, etc.)
    user_intent: Optional[UserIntent] = None

    # Information about the meeting being scheduled
    meeting_details: MeetingFindings = Field(default_factory=MeetingFindings)

    ai_prompt_input: Optional[str] = None

    # Human input
    human_input: Optional[str] = None

    # TODO: revisit this
    # Whether the human input has been processed
    setup_human_input: Optional[bool] = False

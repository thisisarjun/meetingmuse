from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"
    RESUMED = "resumed"


class ActiveConversation(BaseModel):
    started_at: str
    message_count: int
    status: ConversationStatus
    last_activity: Optional[str] = None
    ended_at: Optional[str] = None
    session_id: Optional[str] = None
    authenticated: Optional[bool] = None

"""
Message Protocol Definitions
Defines the message format and validation for WebSocket communication
"""
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class MessageType(StrEnum):
    """Message type identifier"""

    USER_MESSAGE = "user_message"
    BOT_RESPONSE = "bot_response"
    SYSTEM_MESSAGE = "system_message"
    ERROR_MESSAGE = "error_message"


class BaseMessage(BaseModel):
    """Base message format"""

    type: MessageType = Field(..., description="Message type identifier")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp",
    )
    metadata: Optional[dict] = Field(
        default=None, description="Optional additional metadata"
    )


class UserMessage(BaseMessage):
    """Incoming user message format"""

    type: MessageType = Field(
        default=MessageType.USER_MESSAGE, description="Message type identifier"
    )
    content: str = Field(..., description="User message content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp",
    )
    session_id: str = Field(..., description="Session identifier")


class BotResponse(BaseMessage):
    """Outgoing bot response format"""

    type: MessageType = Field(
        default=MessageType.BOT_RESPONSE, description="Message type identifier"
    )
    content: str = Field(..., description="Bot response content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Response timestamp",
    )
    session_id: str = Field(..., description="Session identifier")


class SystemMessage(BaseMessage):
    """System message format"""

    type: MessageType = Field(
        default=MessageType.SYSTEM_MESSAGE, description="Message type identifier"
    )
    content: str = Field(
        ...,
        description="System message content (connection_established|processing|conversation_resumed|waiting_for_input|processing_step)",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp",
    )


class ErrorMessage(BaseMessage):
    """Error message format"""

    type: MessageType = Field(
        default=MessageType.ERROR_MESSAGE, description="Message type identifier"
    )
    error_code: str = Field(..., description="Error code identifier")
    content: str = Field(..., description="Human-readable error message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp",
    )
    retry_suggested: bool = Field(
        default=True, description="Whether client should retry"
    )

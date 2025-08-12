"""
Message Protocol Definitions
Defines the message format and validation for WebSocket communication
"""
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UserMessage(BaseModel):
    """Incoming user message format"""

    type: str = Field(default="user_message", description="Message type identifier")
    content: str = Field(..., description="User message content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp",
    )
    session_id: str = Field(..., description="Session identifier")


class BotResponse(BaseModel):
    """Outgoing bot response format"""

    content: str = Field(..., description="Bot response content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Response timestamp",
    )
    session_id: str = Field(..., description="Session identifier")


class SystemMessage(BaseModel):
    """System message format"""

    type: str = Field(default="system", description="Message type identifier")
    content: str = Field(
        ...,
        description="System message content (connection_established|processing|conversation_resumed|waiting_for_input|processing_step)",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp",
    )
    metadata: Optional[dict] = Field(
        default=None, description="Optional additional metadata"
    )


class ErrorMessage(BaseModel):
    """Error message format"""

    type: str = Field(default="error", description="Message type identifier")
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp",
    )
    retry_suggested: bool = Field(
        default=True, description="Whether client should retry"
    )
    metadata: Optional[dict] = Field(
        default=None, description="Optional additional metadata"
    )

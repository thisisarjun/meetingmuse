"""
Message Protocol Definitions
Defines the message format and validation for WebSocket communication
"""
import json
import logging
import uuid
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


class MessageProtocol:
    """Handles message parsing and validation"""

    @staticmethod
    def parse_user_message(message_text: str) -> Optional[UserMessage]:
        """
        Parse and validate incoming user message

        Args:
            message_text: Raw message text from WebSocket

        Returns:
            UserMessage object if valid, None if invalid
        """
        try:
            message_data = json.loads(message_text)
            return UserMessage(**message_data)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON message: {message_text[:100]}... Error: {str(e)}"
            )
            return None
        except ValueError as e:
            logger.error(
                f"Invalid message data: {message_text[:100]}... Error: {str(e)}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error parsing message: {message_text[:100]}... Error: {str(e)}"
            )
            return None

    @staticmethod
    def create_bot_response(content: str, session_id: str) -> str:
        """
        Create a formatted bot response

        Args:
            content: Response content
            session_id: Session identifier

        Returns:
            JSON string of the bot response
        """
        response = BotResponse(content=content, session_id=session_id)
        return str(response.model_dump_json())

    @staticmethod
    def create_system_message(content: str) -> str:
        """
        Create a formatted system message

        Args:
            content: System message content

        Returns:
            JSON string of the system message
        """
        message = SystemMessage(content=content)
        return str(message.model_dump_json())

    @staticmethod
    def create_error_message(
        error_code: str, message: str, retry_suggested: bool = True
    ) -> str:
        """
        Create a formatted error message

        Args:
            error_code: Error code identifier
            message: Human-readable error message
            retry_suggested: Whether client should retry

        Returns:
            JSON string of the error message
        """
        error_msg = ErrorMessage(
            error_code=error_code, message=message, retry_suggested=retry_suggested
        )
        return str(error_msg.model_dump_json())

    @staticmethod
    def validate_client_id(client_id: str) -> bool:
        """
        Validate client ID format

        Args:
            client_id: Client identifier to validate

        Returns:
            True if valid, False otherwise
        """
        if not client_id or len(client_id.strip()) == 0:
            return False

        # TODO: Implement JWT validation
        if len(client_id) > 100 or len(client_id) < 3:
            return False

        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", client_id):
            return False

        return True

    @staticmethod
    def generate_client_id() -> str:
        """Generate a new unique client ID"""
        return str(uuid.uuid4())

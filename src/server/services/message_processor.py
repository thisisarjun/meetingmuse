import json
import uuid

from server.models.ws_dtos import BotResponse, ErrorMessage, SystemMessage, UserMessage


class MessageProtocol:
    """Handles message parsing and validation"""

    @staticmethod
    def parse_user_message(message_text: str) -> UserMessage:
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
            raise ValueError("Failed to parse json") from e
        except ValueError as e:
            raise ValueError("Invalid message data") from e
        except Exception as e:
            raise Exception("Unexpected error parsing message") from e

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

import json
import re

from server.models.api.ws import UserMessage


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

        if not re.match(r"^[a-zA-Z0-9_-]+$", client_id):
            return False

        return True

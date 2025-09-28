"""
Test suite for SocketMessageProcessor service.
"""
import json
from datetime import datetime

import pytest

from server.models.api.websocket_message import UserMessage
from server.services.socket_message_processor import SocketMessageProcessor


class TestSocketMessageProcessor:
    """Test suite for SocketMessageProcessor."""

    def test_parse_user_message_valid_json(self):
        """Test parsing valid JSON user message."""
        message_data = {
            "type": "user_message",
            "content": "Hello, this is a test message",
            "timestamp": datetime.now().isoformat(),
            "session_id": "test_session_123",
        }
        message_text = json.dumps(message_data)

        result = SocketMessageProcessor.parse_user_message(message_text)

        assert isinstance(result, UserMessage)
        assert result.content == message_data["content"]
        assert result.session_id == message_data["session_id"]
        assert result.type == message_data["type"]

    def test_parse_user_message_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        invalid_json = (
            '{"content": "Hello", "session_id": "test"'  # Missing closing brace
        )

        with pytest.raises(ValueError, match="Failed to parse json"):
            SocketMessageProcessor.parse_user_message(invalid_json)

    def test_parse_user_message_missing_required_fields(self):
        """Test parsing JSON missing required fields raises ValueError."""
        message_data = {
            "content": "Hello"
            # Missing required session_id
        }
        message_text = json.dumps(message_data)

        with pytest.raises(ValueError, match="Invalid message data"):
            SocketMessageProcessor.parse_user_message(message_text)

    @pytest.mark.parametrize(
        "client_id,expected",
        [
            # Valid client IDs
            ("valid_client_123", True),
            ("test-client-456", True),
            # Invalid client IDs
            ("", False),  # Empty
            ("  ", False),  # Only whitespace
            ("ab", False),  # Too short
            ("a" * 101, False),  # Too long
        ],
    )
    def test_validate_client_id_parameterized(self, client_id, expected):
        """Test client ID validation with various inputs."""
        result = SocketMessageProcessor.validate_client_id(client_id)
        assert result == expected

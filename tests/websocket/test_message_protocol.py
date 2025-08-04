"""
Test Message Protocol
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import Mock  # noqa: E402


class MockBaseModel:
    def __init__(self, **kwargs):
        # Set defaults for known models
        if hasattr(self, "_set_defaults"):
            self._set_defaults()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump_json(self):
        return json.dumps(self.__dict__)


class MockField:
    def __init__(self, *args, **kwargs):
        pass


sys.modules["pydantic"] = Mock()
sys.modules["pydantic"].BaseModel = MockBaseModel
sys.modules["pydantic"].Field = MockField

from server.message_protocol import MessageProtocol  # noqa: E402


class TestMessageProtocol:
    """Test cases for MessageProtocol class"""

    def test_validate_client_id_valid(self):
        """Test valid client ID validation"""
        valid_ids = ["user123", "test-client-1", "client_456", "abc", "user-123_test"]

        for client_id in valid_ids:
            assert MessageProtocol.validate_client_id(client_id) is True

    def test_validate_client_id_invalid(self):
        """Test invalid client ID validation"""
        invalid_ids = [
            "",
            "  ",
            "a",
            "a" * 101,
            "user@test",
            "user.test",
            "user test",
            None,
        ]

        for client_id in invalid_ids:
            assert MessageProtocol.validate_client_id(client_id) is False

    def test_generate_client_id(self):
        """Test client ID generation"""
        client_id = MessageProtocol.generate_client_id()

        assert isinstance(client_id, str)
        assert len(client_id) > 0
        assert MessageProtocol.validate_client_id(client_id) is True

        # Generate multiple IDs to ensure uniqueness
        ids = [MessageProtocol.generate_client_id() for _ in range(10)]
        assert len(set(ids)) == 10  # All should be unique

    def test_parse_user_message_valid(self):
        """Test parsing valid user messages"""
        valid_message = {
            "type": "user_message",
            "content": "Hello, I want to schedule a meeting",
            "timestamp": "2025-01-28T10:30:00Z",
            "session_id": "test-session-123",
        }

        message_text = json.dumps(valid_message)
        parsed = MessageProtocol.parse_user_message(message_text)

        assert parsed is not None

    def test_parse_user_message_invalid_json(self):
        """Test parsing invalid JSON messages"""
        invalid_messages = ["not json", '{"incomplete": json', "", "{}"]

        for message_text in invalid_messages:
            parsed = MessageProtocol.parse_user_message(message_text)
            assert parsed is None

    def test_create_bot_response(self):
        """Test creating bot response"""
        content = "I'll help you schedule that meeting."
        session_id = "test-session-123"

        response = MessageProtocol.create_bot_response(content, session_id)

        assert isinstance(response, str)
        # Parse the JSON to verify structure
        response_data = json.loads(response)
        assert "content" in response_data
        assert "session_id" in response_data
        assert "timestamp" in response_data

    def test_create_system_message(self):
        """Test creating system message"""
        content = "connection_established"

        message = MessageProtocol.create_system_message(content)

        assert isinstance(message, str)
        # Parse the JSON to verify structure
        message_data = json.loads(message)
        assert "type" in message_data
        assert "content" in message_data
        assert "timestamp" in message_data

    def test_create_error_message(self):
        """Test creating error message"""
        error_code = "INVALID_INPUT"
        error_message = "The input format is invalid"
        retry_suggested = False

        message = MessageProtocol.create_error_message(
            error_code, error_message, retry_suggested
        )

        assert isinstance(message, str)
        # Parse the JSON to verify structure
        message_data = json.loads(message)
        assert "type" in message_data
        assert "error_code" in message_data
        assert "message" in message_data
        assert "timestamp" in message_data
        assert "retry_suggested" in message_data

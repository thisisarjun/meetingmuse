"""
Test WebSocket Connection Manager
"""
import json
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

sys.modules["fastapi"] = Mock()
sys.modules["fastapi.responses"] = Mock()
sys.modules["pydantic"] = Mock()
sys.modules["uvicorn"] = Mock()


# Mock Pydantic BaseModel and Field
class MockBaseModel:
    pass


class MockField:
    def __init__(self, *args, **kwargs):
        pass


sys.modules["pydantic"].BaseModel = MockBaseModel
sys.modules["pydantic"].Field = MockField

from server.connection_manager import ConnectionManager  # noqa: E402


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for each test"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket object"""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    return websocket


class TestConnectionManager:
    """Test cases for ConnectionManager class"""

    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager, mock_websocket):
        """Test successful connection establishment"""
        client_id = "test_client_1"

        result = await connection_manager.connect(mock_websocket, client_id)

        assert result is True
        assert client_id in connection_manager.active_connections
        assert client_id in connection_manager.connection_metadata
        assert connection_manager.active_connections[client_id] == mock_websocket

        # Verify websocket.accept was called
        mock_websocket.accept.assert_called_once()

        # Verify system message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "system"
        assert sent_message["content"] == "connection_established"

    @pytest.mark.asyncio
    async def test_connect_websocket_error(self, connection_manager, mock_websocket):
        """Test connection failure when WebSocket accept fails"""
        client_id = "test_client_2"
        mock_websocket.accept.side_effect = Exception("Connection failed")

        result = await connection_manager.connect(mock_websocket, client_id)

        assert result is False
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.connection_metadata

    def test_disconnect_existing_client(self, connection_manager):
        """Test disconnecting an existing client"""
        client_id = "test_client_3"
        mock_websocket = MagicMock()

        # Manually add client to simulate connected state
        connection_manager.active_connections[client_id] = mock_websocket
        connection_manager.connection_metadata[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "message_count": 5,
        }

        result = connection_manager.disconnect(client_id)

        assert result is True
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.connection_metadata

    def test_disconnect_nonexistent_client(self, connection_manager):
        """Test disconnecting a client that doesn't exist"""
        client_id = "nonexistent_client"

        result = connection_manager.disconnect(client_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_personal_message_success(
        self, connection_manager, mock_websocket
    ):
        """Test successful personal message sending"""
        client_id = "test_client_4"
        message = "Hello, test message!"

        # Setup connected client
        connection_manager.active_connections[client_id] = mock_websocket

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is True
        mock_websocket.send_text.assert_called_once()

        # Verify message format
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["content"] == message
        assert sent_data["session_id"] == client_id
        assert "timestamp" in sent_data

    @pytest.mark.asyncio
    async def test_send_personal_message_disconnected_client(self, connection_manager):
        """Test sending message to disconnected client"""
        client_id = "disconnected_client"
        message = "This should fail"

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_system_message(self, connection_manager, mock_websocket):
        """Test sending system message"""
        client_id = "test_client_5"
        system_type = "processing"

        # Setup connected client
        connection_manager.active_connections[client_id] = mock_websocket

        result = await connection_manager.send_system_message(client_id, system_type)

        assert result is True
        mock_websocket.send_text.assert_called_once()

        # Verify message format
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "system"
        assert sent_data["content"] == system_type
        assert "timestamp" in sent_data

    @pytest.mark.asyncio
    async def test_send_error_message(self, connection_manager, mock_websocket):
        """Test sending error message"""
        client_id = "test_client_6"
        error_code = "TEST_ERROR"
        error_message = "This is a test error"

        # Setup connected client
        connection_manager.active_connections[client_id] = mock_websocket

        result = await connection_manager.send_error_message(
            client_id, error_code, error_message, retry_suggested=False
        )

        assert result is True
        mock_websocket.send_text.assert_called_once()

        # Verify message format
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "error"
        assert sent_data["error_code"] == error_code
        assert sent_data["message"] == error_message
        assert sent_data["retry_suggested"] is False
        assert "timestamp" in sent_data

    @pytest.mark.asyncio
    async def test_broadcast_message(self, connection_manager):
        """Test broadcasting message to multiple clients"""
        message = "Broadcast test message"

        # Setup multiple clients
        clients = ["client_1", "client_2", "client_3"]
        mock_websockets = []

        for client_id in clients:
            mock_ws = AsyncMock()
            mock_websockets.append(mock_ws)
            connection_manager.active_connections[client_id] = mock_ws

        result = await connection_manager.broadcast(message)

        assert result == 3  # All clients should receive the message

        # Verify all websockets received the message
        for mock_ws in mock_websockets:
            mock_ws.send_text.assert_called_once()

    def test_get_connection_count(self, connection_manager):
        """Test getting connection count"""
        assert connection_manager.get_connection_count() == 0

        # Add some clients
        connection_manager.active_connections["client_1"] = MagicMock()
        connection_manager.active_connections["client_2"] = MagicMock()

        assert connection_manager.get_connection_count() == 2

    def test_get_client_info(self, connection_manager):
        """Test getting client information"""
        client_id = "test_client_7"
        metadata = {"connected_at": datetime.now().isoformat(), "message_count": 10}

        connection_manager.connection_metadata[client_id] = metadata

        result = connection_manager.get_client_info(client_id)
        assert result == metadata

        # Test nonexistent client
        result = connection_manager.get_client_info("nonexistent")
        assert result is None

    def test_list_active_clients(self, connection_manager):
        """Test listing active clients"""
        clients = ["client_1", "client_2", "client_3"]

        for client_id in clients:
            connection_manager.active_connections[client_id] = MagicMock()

        active_clients = connection_manager.list_active_clients()

        assert set(active_clients) == set(clients)

    def test_increment_message_count(self, connection_manager):
        """Test incrementing message count for a client"""
        client_id = "test_client_8"
        connection_manager.connection_metadata[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "message_count": 0,
        }

        connection_manager.increment_message_count(client_id)
        assert connection_manager.connection_metadata[client_id]["message_count"] == 1

        connection_manager.increment_message_count(client_id)
        assert connection_manager.connection_metadata[client_id]["message_count"] == 2

        # Test nonexistent client (should not raise error)
        connection_manager.increment_message_count("nonexistent")

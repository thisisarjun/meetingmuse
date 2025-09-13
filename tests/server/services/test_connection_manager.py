"""
Test suite for ConnectionManager WebSocket service.
"""
from datetime import datetime

import pytest
from fastapi import WebSocketDisconnect

from server.constants import SystemMessageTypes
from server.models.connections import ConnectionMetadataDto


class TestConnectionManager:
    """Test suite for ConnectionManager."""

    async def test_connect_success(self, connection_manager, mock_websocket):
        """Test successful WebSocket connection."""
        client_id = "test_client_123"

        result = await connection_manager.connect(mock_websocket, client_id)

        assert result is True
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        assert client_id in connection_manager.connection_metadata

        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()

        metadata = connection_manager.connection_metadata[client_id]
        assert isinstance(metadata, ConnectionMetadataDto)
        assert metadata.message_count == 0
        assert metadata.connected_at is not None

    async def test_connect_with_session_id(self, connection_manager, mock_websocket):
        """Test WebSocket connection with session ID."""
        client_id = "test_client_123"
        session_id = "session_456"

        result = await connection_manager.connect(mock_websocket, client_id, session_id)

        assert result is True
        assert client_id in connection_manager.active_connections
        mock_websocket.accept.assert_called_once()

    async def test_connect_websocket_accept_failure(
        self, connection_manager, mock_websocket
    ):
        """Test connection failure when WebSocket accept fails."""
        client_id = "test_client_123"
        mock_websocket.accept.side_effect = Exception("Accept failed")

        result = await connection_manager.connect(mock_websocket, client_id)

        assert result is False
        assert client_id not in connection_manager.active_connections
        assert client_id not in connection_manager.connection_metadata

    async def test_send_personal_message_success(
        self, connection_manager, mock_websocket
    ):
        """Test sending a personal message successfully."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        message = "Hello, test message!"

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is True
        mock_websocket.send_text.assert_called_once()

        call_args = mock_websocket.send_text.call_args[0][0]
        import json

        sent_message = json.loads(call_args)
        assert sent_message["content"] == message
        assert sent_message["session_id"] == client_id

    async def test_send_personal_message_to_disconnected_client(
        self, connection_manager
    ):
        """Test sending message to disconnected client."""
        client_id = "disconnected_client"
        message = "Hello, test message!"

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is False

    async def test_send_personal_message_websocket_disconnect(
        self, connection_manager, mock_websocket
    ):
        """Test handling WebSocketDisconnect during message send."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        connection_manager.connection_metadata[client_id] = ConnectionMetadataDto(
            connected_at=datetime.now().isoformat(), message_count=0
        )
        mock_websocket.send_text.side_effect = WebSocketDisconnect()
        message = "Hello, test message!"

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is False
        assert client_id not in connection_manager.active_connections

    async def test_send_personal_message_general_exception(
        self, connection_manager, mock_websocket
    ):
        """Test handling general exception during message send."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        mock_websocket.send_text.side_effect = Exception("Send failed")
        message = "Hello, test message!"

        result = await connection_manager.send_personal_message(message, client_id)

        assert result is False

    async def test_send_system_message_success(
        self, connection_manager, mock_websocket
    ):
        """Test sending system message successfully."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        system_type = SystemMessageTypes.CONNECTION_ESTABLISHED
        additional_data = {"key": "value"}

        result = await connection_manager.send_system_message(
            client_id, system_type, additional_data
        )

        assert result is True
        mock_websocket.send_text.assert_called_once()

    async def test_send_system_message_to_disconnected_client(self, connection_manager):
        """Test sending system message to disconnected client."""
        client_id = "disconnected_client"
        system_type = SystemMessageTypes.CONNECTION_ESTABLISHED

        result = await connection_manager.send_system_message(client_id, system_type)

        assert result is False

    async def test_send_system_message_exception(
        self, connection_manager, mock_websocket
    ):
        """Test handling exception during system message send."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        mock_websocket.send_text.side_effect = Exception("Send failed")
        system_type = SystemMessageTypes.CONNECTION_ESTABLISHED

        result = await connection_manager.send_system_message(client_id, system_type)

        assert result is False

    async def test_send_error_message_success(self, connection_manager, mock_websocket):
        """Test sending error message successfully."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        error_code = "TEST_ERROR"
        message = "Test error message"
        additional_metadata = {"debug_info": "test"}

        result = await connection_manager.send_error_message(
            client_id, error_code, message, True, additional_metadata
        )

        assert result is True
        mock_websocket.send_text.assert_called_once()

    async def test_send_error_message_to_disconnected_client(self, connection_manager):
        """Test sending error message to disconnected client."""
        client_id = "disconnected_client"
        error_code = "TEST_ERROR"
        message = "Test error message"

        result = await connection_manager.send_error_message(
            client_id, error_code, message
        )

        assert result is False

    async def test_send_error_message_exception(
        self, connection_manager, mock_websocket
    ):
        """Test handling exception during error message send."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket
        mock_websocket.send_text.side_effect = Exception("Send failed")
        error_code = "TEST_ERROR"
        message = "Test error message"

        result = await connection_manager.send_error_message(
            client_id, error_code, message
        )

        assert result is False

    def test_get_client_info_existing_client(self, connection_manager):
        """Test getting client info for existing client."""
        client_id = "test_client_123"
        metadata = ConnectionMetadataDto(
            connected_at=datetime.now().isoformat(), message_count=5
        )
        connection_manager.connection_metadata[client_id] = metadata

        result = connection_manager.get_client_info(client_id)

        assert result == metadata

    def test_get_client_info_nonexistent_client(self, connection_manager):
        """Test getting client info for non-existent client."""
        client_id = "nonexistent_client"

        result = connection_manager.get_client_info(client_id)

        assert result is None

    def test_list_active_clients(self, connection_manager, mock_websocket):
        """Test listing active clients."""
        connection_manager.active_connections["client1"] = mock_websocket
        connection_manager.active_connections["client2"] = mock_websocket

        result = connection_manager.list_active_clients()

        assert set(result) == {"client1", "client2"}

    def test_list_active_clients_empty(self, connection_manager):
        """Test listing active clients when none are connected."""
        result = connection_manager.list_active_clients()

        assert result == []

    def test_increment_message_count_existing_client(self, connection_manager):
        """Test incrementing message count for existing client."""
        client_id = "test_client_123"
        connection_manager.connection_metadata[client_id] = ConnectionMetadataDto(
            connected_at=datetime.now().isoformat(), message_count=0
        )

        connection_manager.increment_message_count(client_id)

        assert connection_manager.connection_metadata[client_id].message_count == 1

    def test_increment_message_count_nonexistent_client(self, connection_manager):
        """Test incrementing message count for non-existent client doesn't raise error."""
        client_id = "nonexistent_client"

        connection_manager.increment_message_count(client_id)

        assert client_id not in connection_manager.connection_metadata

    def test_get_active_connections_count(self, connection_manager, mock_websocket):
        """Test getting active connections count."""
        connection_manager.active_connections["client1"] = mock_websocket
        connection_manager.active_connections["client2"] = mock_websocket

        result = connection_manager.get_active_connections()

        assert result == 2

    def test_get_active_connections_count_empty(self, connection_manager):
        """Test getting active connections count when empty."""
        result = connection_manager.get_active_connections()

        assert result == 0

    @pytest.mark.parametrize(
        "system_type,additional_data",
        [
            (SystemMessageTypes.CONNECTION_ESTABLISHED, None),
            (SystemMessageTypes.PROCESSING, {"step": "analyzing"}),
            (SystemMessageTypes.CONVERSATION_RESUMED, {"previous_count": 5}),
            (SystemMessageTypes.WAITING_FOR_INPUT, None),
        ],
    )
    async def test_send_system_message_types(
        self, connection_manager, mock_websocket, system_type, additional_data
    ):
        """Test sending different types of system messages."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket

        result = await connection_manager.send_system_message(
            client_id, system_type, additional_data
        )

        assert result is True
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.parametrize(
        "retry_suggested",
        [
            True,
            False,
        ],
    )
    async def test_send_error_message_retry_flags(
        self, connection_manager, mock_websocket, retry_suggested
    ):
        """Test error message with different retry flags."""
        client_id = "test_client_123"
        connection_manager.active_connections[client_id] = mock_websocket

        result = await connection_manager.send_error_message(
            client_id, "TEST_ERROR", "Test message", retry_suggested
        )

        assert result is True
        mock_websocket.send_text.assert_called_once()

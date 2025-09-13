"""
Shared test fixtures for server tests.
"""
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket

from server.models.connections import ConnectionMetadataDto
from server.services.connection_manager import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a ConnectionManager instance for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    return websocket


@pytest.fixture
def connection_metadata():
    """Create sample connection metadata for testing."""
    return ConnectionMetadataDto(
        connected_at=datetime.now().isoformat(), message_count=5
    )

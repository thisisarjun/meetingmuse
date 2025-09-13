"""
Shared test fixtures for server tests.
"""
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket

from common.logger.logger import Logger
from meetingmuse.graph.graph_message_processor import GraphMessageProcessor
from server.models.connections import ConnectionMetadataDto
from server.models.conversation import ActiveConversation, ConversationStatus
from server.services.connection_manager import ConnectionManager
from server.services.conversation_manager import ConversationManager


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


@pytest.fixture
def mock_logger():
    """Create a mock Logger for testing."""
    return Mock(spec=Logger)


@pytest.fixture
def mock_message_processor():
    """Create a mock GraphMessageProcessor for testing."""
    processor = Mock(spec=GraphMessageProcessor)
    processor.get_conversation_state = AsyncMock()
    return processor


@pytest.fixture
def conversation_manager(mock_logger, mock_message_processor):
    """Create a ConversationManager instance for testing."""
    return ConversationManager(mock_logger, mock_message_processor)


@pytest.fixture
def active_conversation():
    """Create sample active conversation for testing."""
    return ActiveConversation(
        started_at=datetime.now().isoformat(),
        last_activity=datetime.now().isoformat(),
        message_count=3,
        status=ConversationStatus.ACTIVE,
        session_id="session_123",
        authenticated=True,
    )

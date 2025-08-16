"""
Shared test fixtures for meetingmuse tests.
"""
from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from common.logger import Logger
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState, UserIntent


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=Logger)


@pytest.fixture
def mock_graph():
    """Create a mock CompiledStateGraph for testing."""
    mock_graph = Mock(spec=CompiledStateGraph)
    mock_graph.ainvoke = AsyncMock()
    mock_graph.astream = AsyncMock()
    mock_graph.get_state = Mock()
    return mock_graph


@pytest.fixture
def sample_meeting_muse_state():
    """Create a sample MeetingMuseBotState for testing."""
    return MeetingMuseBotState(
        messages=[
            HumanMessage(content="I need to schedule a meeting"),
            AIMessage(
                content="I'd be happy to help you schedule a meeting. Could you please provide more details?"
            ),
        ],
        user_intent=UserIntent.SCHEDULE_MEETING,
        meeting_details=MeetingFindings(),
    )


@pytest.fixture
def empty_meeting_muse_state():
    """Create an empty MeetingMuseBotState for testing."""
    return MeetingMuseBotState(messages=[], meeting_details=MeetingFindings())


@pytest.fixture
def state_with_only_human_message():
    """Create a state with only a human message."""
    return MeetingMuseBotState(
        messages=[HumanMessage(content="Hello, I need help")],
        meeting_details=MeetingFindings(),
    )


@pytest.fixture
def state_with_only_ai_message():
    """Create a state with only an AI message."""
    return MeetingMuseBotState(
        messages=[AIMessage(content="How can I help you today?")],
        meeting_details=MeetingFindings(),
    )

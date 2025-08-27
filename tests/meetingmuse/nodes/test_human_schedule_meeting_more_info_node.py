from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import HumanMessage

from common.logger import Logger
from meetingmuse.models.interrupts import InterruptInfo, InterruptType
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, OperationStatus
from meetingmuse.nodes.human_schedule_meeting_more_info_node import (
    HumanScheduleMeetingMoreInfoNode,
)


class TestHumanScheduleMeetingMoreInfoNode:
    """Base test class for HumanScheduleMeetingMoreInfoNode with shared fixtures."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def node(self, mock_logger):
        """Create a HumanScheduleMeetingMoreInfoNode instance with mocked logger."""
        return HumanScheduleMeetingMoreInfoNode(mock_logger)

    @pytest.fixture
    def sample_state(self):
        """Create a sample state for testing."""
        return MeetingMuseBotState(
            messages=[],
            meeting_details=MeetingFindings(
                title="Team Standup",
                date_time=None,
                participants=["john@example.com"],
                duration=None,
            ),
            operation_status=OperationStatus(
                status=False,
                error_message=None,
                ai_prompt_input="Please provide the missing meeting details.",
            ),
        )


class TestNodeName(TestHumanScheduleMeetingMoreInfoNode):
    """Test suite for HumanScheduleMeetingMoreInfoNode.node_name property."""

    def test_node_name_returns_correct_value(self, node):
        """Test that node_name property returns the correct NodeName."""
        # Act
        result = node.node_name

        # Assert
        assert result == NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO


class TestNodeAction(TestHumanScheduleMeetingMoreInfoNode):
    """Test suite for HumanScheduleMeetingMoreInfoNode.node_action method."""

    @patch("meetingmuse.nodes.human_schedule_meeting_more_info_node.interrupt")
    def test_node_action_with_valid_human_input(
        self, mock_interrupt, node, mock_logger, sample_state
    ):
        """Test node_action with valid human input proceeds to collecting_info."""
        # Arrange
        mock_interrupt.return_value = "The meeting should be at 2:00 PM for 1 hour"
        initial_message_count = len(sample_state.messages)

        # Act
        result = node.node_action(sample_state)

        # Assert
        # Verify interrupt was called with the ai_prompt_input
        interrupt_info = InterruptInfo(
            type=InterruptType.SEEK_MORE_INFO,
            message="Need more information to schedule the meeting",
            question="Please provide the missing meeting details.",
        )
        mock_interrupt.assert_called_once_with(interrupt_info)

        # Verify human message was added to state
        assert len(sample_state.messages) == initial_message_count + 1
        assert isinstance(sample_state.messages[-1], HumanMessage)
        assert (
            sample_state.messages[-1].content
            == "The meeting should be at 2:00 PM for 1 hour"
        )

        # Verify ai_prompt_input was cleared
        assert sample_state.operation_status.ai_prompt_input is None

        # Verify state is returned (not a command)
        assert result is sample_state

    @patch("meetingmuse.nodes.human_schedule_meeting_more_info_node.interrupt")
    def test_node_action_with_empty_human_input(
        self, mock_interrupt, node, mock_logger, sample_state
    ):
        """Test node_action with empty human input returns to same node."""
        # Arrange
        mock_interrupt.return_value = ""
        initial_message_count = len(sample_state.messages)
        initial_ai_prompt = sample_state.operation_status.ai_prompt_input

        # Act
        result = node.node_action(sample_state)

        # Assert
        # Verify interrupt was called
        interrupt_info = InterruptInfo(
            type=InterruptType.SEEK_MORE_INFO,
            message="Need more information to schedule the meeting",
            question="Please provide the missing meeting details.",
        )
        mock_interrupt.assert_called_once_with(interrupt_info)

        # Verify logger calls - since we're using a mock logger, prefixes aren't applied
        mock_logger.info.assert_any_call("Received human input: ")
        mock_logger.info.assert_any_call("No input provided, asking again")

        # Verify no message was added to state
        assert len(sample_state.messages) == initial_message_count

        # Verify ai_prompt_input was not cleared
        assert sample_state.operation_status.ai_prompt_input == initial_ai_prompt

        # Verify state is returned (not a command)
        assert isinstance(result, MeetingMuseBotState)
        assert result == sample_state

    @patch("meetingmuse.nodes.human_schedule_meeting_more_info_node.interrupt")
    def test_node_action_with_whitespace_only_input(
        self, mock_interrupt, node, mock_logger, sample_state
    ):
        """Test node_action with whitespace-only input returns to same node."""
        # Arrange
        mock_interrupt.return_value = "   \n\t  "
        initial_message_count = len(sample_state.messages)

        # Act
        result = node.node_action(sample_state)

        # Assert
        # Verify logger calls
        mock_logger.info.assert_any_call("Received human input:    \n\t  ")
        mock_logger.info.assert_any_call("No input provided, asking again")

        # Verify no message was added to state
        assert len(sample_state.messages) == initial_message_count

        # Verify state is returned (not a command)
        assert isinstance(result, MeetingMuseBotState)
        assert result == sample_state

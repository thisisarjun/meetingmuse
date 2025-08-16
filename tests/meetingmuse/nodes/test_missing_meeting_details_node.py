from unittest.mock import Mock

import pytest

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, OperationStatus
from meetingmuse.nodes.prompt_missing_meeting_details_node import (
    PromptMissingMeetingDetailsNode,
)
from meetingmuse.services.meeting_details_service import MeetingDetailsService


class TestPromptMissingMeetingDetailsNode:
    """Base test class for PromptMissingMeetingDetailsNode with shared fixtures."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def meeting_service(self, mock_logger):
        """Create a real MeetingDetailsService instance for testing."""
        model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
        return MeetingDetailsService(model, mock_logger)

    @pytest.fixture
    def node(self, mock_logger, meeting_service):
        """Create a PromptMissingMeetingDetailsNode instance with real meeting service."""
        return PromptMissingMeetingDetailsNode(meeting_service, mock_logger)

    @pytest.fixture
    def complete_meeting_state(self):
        """Create a state with complete meeting details."""
        return MeetingMuseBotState(
            messages=[],
            meeting_details=MeetingFindings(
                title="Team Standup",
                date_time="2024-01-15 10:00 AM",
                participants=["john@example.com", "jane@example.com"],
                duration="30 minutes",
            ),
            operation_status=OperationStatus(
                status=False,
                error_message=None,
                ai_prompt_input=None,
            ),
        )

    @pytest.fixture
    def incomplete_meeting_state(self):
        """Create a state with incomplete meeting details."""
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
                ai_prompt_input=None,
            ),
        )


class TestNodeName(TestPromptMissingMeetingDetailsNode):
    """Test suite for PromptMissingMeetingDetailsNode.node_name property."""

    def test_node_name_returns_correct_value(self, node):
        """Test that node_name property returns the correct NodeName."""
        # Act
        result = node.node_name

        # Assert
        assert result == NodeName.PROMPT_MISSING_MEETING_DETAILS


class TestNodeActionWithCompleteMeetingDetails(TestPromptMissingMeetingDetailsNode):
    """Test suite for node_action when meeting details are complete."""

    def test_node_action_with_complete_details_returns_end_command(
        self, node, complete_meeting_state
    ):
        """Test node_action returns END command when all required fields are present."""
        # Act
        result = node.node_action(complete_meeting_state)

        # Assert
        assert isinstance(result, MeetingMuseBotState)
        assert result == complete_meeting_state

    def test_node_action_with_complete_details_does_not_modify_ai_prompt_input(
        self, node, complete_meeting_state
    ):
        """Test that ai_prompt_input is not modified when details are complete."""
        # Arrange
        original_ai_prompt_input = (
            complete_meeting_state.operation_status.ai_prompt_input
        )

        # Act
        node.node_action(complete_meeting_state)

        # Assert
        assert (
            complete_meeting_state.operation_status.ai_prompt_input
            == original_ai_prompt_input
        )


class TestNodeActionWithIncompleteMeetingDetails(TestPromptMissingMeetingDetailsNode):
    """Test suite for node_action when meeting details are incomplete."""

    @pytest.mark.skip(reason="live call to LLM")
    def test_node_action_with_missing_fields_sets_ai_prompt_input(
        self, node, incomplete_meeting_state
    ):
        """Test that ai_prompt_input is set with a response when fields are missing."""
        # Arrange
        original_ai_prompt_input = (
            incomplete_meeting_state.operation_status.ai_prompt_input
        )

        # Act
        node.node_action(incomplete_meeting_state)

        # Assert
        assert (
            incomplete_meeting_state.operation_status.ai_prompt_input
            != original_ai_prompt_input
        )
        assert incomplete_meeting_state.operation_status.ai_prompt_input is not None
        assert isinstance(
            incomplete_meeting_state.operation_status.ai_prompt_input, str
        )
        assert len(incomplete_meeting_state.operation_status.ai_prompt_input) > 0

from unittest.mock import Mock

import pytest

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode


class TestCollectingInfoNode:
    """Base test class for CollectingInfoNode with shared fixtures."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def node(self, mock_logger):
        """Create a CollectingInfoNode instance with real HuggingFace model and mocked logger."""
        model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
        return CollectingInfoNode(model, mock_logger)


class TestGetNextNodeName(TestCollectingInfoNode):
    """Test suite for CollectingInfoNode.get_next_node_name method."""

    @pytest.mark.parametrize(
        "meeting_details,expected_result,test_description",
        [
            # Complete meeting details should return END
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration="30 minutes",
                ),
                NodeName.SCHEDULE_MEETING,
                "all required fields present",
            ),
            # Missing individual required fields should return PROMPT_MISSING_MEETING_DETAILS
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time=None,  # Missing date_time
                    participants=["john@example.com", "jane@example.com"],
                    duration="30 minutes",
                ),
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "missing date_time",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=[],  # Empty participants list
                    duration="30 minutes",
                ),
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "empty participants list",
            ),
            (
                MeetingFindings(),
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "empty meeting details",
            ),
        ],
    )
    def test_get_next_node_name_with_meeting_details(
        self, node, meeting_details, expected_result, test_description
    ):
        """
        Test get_next_node_name returns correct NodeName based on meeting details completeness.

        This parameterized test covers various scenarios of complete and incomplete meeting details.
        """
        # Arrange
        state = MeetingMuseBotState(messages=[], meeting_details=meeting_details)

        # Act
        result = node.get_next_node_name(state)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"


class TestIsMeetingDetailsComplete(TestCollectingInfoNode):
    """Test suite for CollectingInfoNode.meeting_service.is_meeting_details_complete method."""

    @pytest.mark.parametrize(
        "meeting_details,expected_result,test_description",
        [
            # Complete meeting details should return True
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration="30 minutes",
                ),
                True,
                "all required fields present",
            ),
            # Missing individual required fields should return False
            (
                MeetingFindings(
                    title=None,  # Missing title
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration="30 minutes",
                ),
                False,
                "missing title",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=[],  # Empty participants list
                    duration="30 minutes",
                ),
                False,
                "empty participants list",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=None,  # Missing duration
                ),
                False,
                "missing duration",
            ),
            (MeetingFindings(), False, "empty meeting details"),
        ],
    )
    def test_is_meeting_details_complete(
        self, node, meeting_details, expected_result, test_description
    ):
        """
        Test is_meeting_details_complete returns correct boolean based on meeting details completeness.

        This parameterized test covers various scenarios of complete and incomplete meeting details.
        """
        # Act
        result = node.meeting_service.is_meeting_details_complete(meeting_details)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"


class TestUpdateStateMeetingDetails(TestCollectingInfoNode):
    """Test suite for CollectingInfoNode.meeting_service.update_state_meeting_details method."""

    @pytest.mark.parametrize(
        "initial_state_details,new_meeting_details,expected_state_details,test_description",
        [
            # Update empty state with new details
            (
                MeetingFindings(),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                ),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                ),
                "update empty state with complete details",
            ),
            # Partial update - only add missing fields
            (
                MeetingFindings(title="Team Standup", date_time="2024-01-15 10:00 AM"),
                MeetingFindings(
                    participants=["john@example.com"], duration="30 minutes"
                ),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                ),
                "partial update adding missing fields",
            ),
            # Update existing fields
            (
                MeetingFindings(
                    title="Old Meeting",
                    date_time="2024-01-15 10:00 AM",
                    participants=["old@example.com"],
                    duration="60 minutes",
                ),
                MeetingFindings(title="New Meeting", participants=["new@example.com"]),
                MeetingFindings(
                    title="New Meeting",
                    date_time="2024-01-15 10:00 AM",
                    participants=["new@example.com"],
                    duration="60 minutes",
                ),
                "update existing fields keeping others unchanged",
            ),
            # None values should not update existing fields
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                ),
                MeetingFindings(
                    title=None, date_time=None, location="Conference Room A"
                ),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                    location="Conference Room A",
                ),
                "none values do not overwrite existing fields",
            ),
        ],
    )
    def test_update_state_meeting_details(
        self,
        node,
        initial_state_details,
        new_meeting_details,
        expected_state_details,
        test_description,
    ):
        """
        Test update_state_meeting_details correctly updates state with new meeting details.

        This parameterized test covers various scenarios of updating meeting details.
        """
        # Arrange
        state = MeetingMuseBotState(messages=[], meeting_details=initial_state_details)

        # Act
        result_state = node.meeting_service.update_state_meeting_details(
            new_meeting_details, state
        )

        # Assert - result_state is actually a MeetingFindings object, not a state
        assert (
            result_state.title == expected_state_details.title
        ), f"Title mismatch for case: {test_description}"
        assert (
            result_state.date_time == expected_state_details.date_time
        ), f"Date time mismatch for case: {test_description}"
        assert (
            result_state.participants == expected_state_details.participants
        ), f"Participants mismatch for case: {test_description}"
        assert (
            result_state.duration == expected_state_details.duration
        ), f"Duration mismatch for case: {test_description}"
        assert (
            result_state.location == expected_state_details.location
        ), f"Location mismatch for case: {test_description}"

        # Note: The method now returns a MeetingFindings object, not the state object


class TestInvokeExtractionPrompt(TestCollectingInfoNode):
    """Test suite for CollectingInfoNode.invoke_extraction_prompt method."""

    @pytest.mark.skip(reason="live call to LLM")
    @pytest.mark.parametrize(
        "meeting_details,missing_required,user_input,expected_result,test_description",
        [
            (
                MeetingFindings(
                    participants=["john@example.com"],
                ),
                ["title", "date_time", "duration"],
                "Team Standup meeting on 2024-01-15 at 10:00 AM for 30 minutes",
                MeetingFindings(
                    title="Team Standup meeting",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration="30 minutes",
                ),
                "extraction prompt returns correct meeting details",
            ),
        ],
    )
    def test_invoke_extraction_prompt(
        self,
        node,
        meeting_details,
        missing_required,
        user_input,
        expected_result,
        test_description,
    ):
        """
        Test invoke_extraction_prompt returns correct meeting details based on user input.
        """
        # Act
        result = node.invoke_extraction_prompt(
            meeting_details, missing_required, user_input
        )

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"


class TestInvokeMissingFieldsPrompt(TestCollectingInfoNode):
    """Test suite for CollectingInfoNode.meeting_service.invoke_missing_fields_prompt method."""

    @pytest.mark.skip(reason="live call to LLM")
    @pytest.mark.parametrize(
        "state,expected_result,test_description",
        [
            (
                MeetingMuseBotState(
                    messages=[],
                    meeting_details=MeetingFindings(
                        # title="Team Standup",
                        date_time="2024-01-15 10:00 AM",
                        participants=["john@example.com"],
                        duration="30 minutes",
                    ),
                ),
                "I need some more information to schedule your meeting. Could you provide the missing details?",
                "invoke missing fields prompt returns correct response",
            ),
        ],
    )
    def test_invoke_missing_fields_prompt(
        self, node, state, expected_result, test_description
    ):
        """
        Test invoke_missing_fields_prompt returns correct response based on state.
        """
        # Act
        result = node.meeting_service.invoke_missing_fields_prompt(state)
        print(result)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"

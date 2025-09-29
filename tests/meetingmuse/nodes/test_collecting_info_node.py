import pytest

from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode


class TestGetNextNodeName:
    """Test suite for CollectingInfoNode.get_next_node_name method."""

    @pytest.mark.parametrize(
        "meeting_details,user_intent,expected_result,test_description",
        [
            # Complete meeting details should return SCHEDULE_MEETING
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                NodeName.SCHEDULE_MEETING,
                "all required fields present for meeting",
            ),
            # Missing individual required fields should return PROMPT_MISSING_MEETING_DETAILS
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time=None,  # Missing date_time
                    participants=["john@example.com", "jane@example.com"],
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "missing date_time for meeting",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=[],  # Empty participants list
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "empty participants list for meeting",
            ),
            (
                MeetingFindings(),
                UserIntent.SCHEDULE_MEETING,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "empty meeting details for meeting",
            ),
            # Complete reminder details should return SCHEDULE_MEETING
            (
                MeetingFindings(
                    title="Doctor Appointment",
                    date_time="2024-01-15 10:00 AM",
                ),
                UserIntent.REMINDER,
                NodeName.SCHEDULE_MEETING,
                "all required fields present for reminder",
            ),
            # Missing individual required fields for reminder should return PROMPT_MISSING_MEETING_DETAILS
            (
                MeetingFindings(
                    title="Doctor Appointment",
                    date_time=None,  # Missing date_time
                ),
                UserIntent.REMINDER,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "missing date_time for reminder",
            ),
            (
                MeetingFindings(
                    title=None,  # Missing title
                    date_time="2024-01-15 10:00 AM",
                ),
                UserIntent.REMINDER,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "missing title for reminder",
            ),
            (
                MeetingFindings(),
                UserIntent.REMINDER,
                NodeName.PROMPT_MISSING_MEETING_DETAILS,
                "empty reminder details",
            ),
        ],
    )
    def test_get_next_node_name_with_meeting_details(
        self,
        collecting_info_node: CollectingInfoNode,
        meeting_details: MeetingFindings,
        user_intent: UserIntent,
        expected_result: NodeName,
        test_description: str,
    ):
        """
        Test get_next_node_name returns correct NodeName based on meeting details completeness.

        This parameterized test covers various scenarios of complete and incomplete meeting details.
        """
        # Arrange
        state = MeetingMuseBotState(
            messages=[],
            meeting_details=meeting_details,
            user_intent=user_intent,
        )

        # Act
        result = collecting_info_node.get_next_node_name(state)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"


class TestIsMeetingDetailsComplete:
    """Test suite for CollectingInfoNode service.is_details_complete method."""

    @pytest.mark.parametrize(
        "meeting_details,user_intent,expected_result,test_description",
        [
            # Complete meeting details should return True
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                True,
                "all required fields present for meeting",
            ),
            # Missing individual required fields should return False
            (
                MeetingFindings(
                    title=None,  # Missing title
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                False,
                "missing title for meeting",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=[],  # Empty participants list
                    duration=30,
                ),
                UserIntent.SCHEDULE_MEETING,
                False,
                "empty participants list for meeting",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=None,  # Missing duration
                ),
                UserIntent.SCHEDULE_MEETING,
                False,
                "missing duration for meeting",
            ),
            (
                MeetingFindings(),
                UserIntent.SCHEDULE_MEETING,
                False,
                "empty meeting details for meeting",
            ),
            # Complete reminder details should return True
            (
                MeetingFindings(
                    title="Doctor Appointment",
                    date_time="2024-01-15 10:00 AM",
                ),
                UserIntent.REMINDER,
                True,
                "all required fields present for reminder",
            ),
            # Reminder with extra fields should still return True if required fields are present
            (
                MeetingFindings(
                    title="Doctor Appointment",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],  # Extra field
                    duration=30,  # Extra field
                ),
                UserIntent.REMINDER,
                True,
                "reminder with extra fields but required fields present",
            ),
        ],
    )
    def test_is_details_complete(
        self,
        collecting_info_node,
        meeting_details,
        user_intent,
        expected_result,
        test_description,
    ):
        """
        Test is_details_complete returns correct boolean based on meeting details completeness.

        This parameterized test covers various scenarios of complete and incomplete meeting details
        for both meeting scheduling and reminder intents.
        """
        # Arrange - Mock the state to set user intent
        state = MeetingMuseBotState(
            messages=[],
            meeting_details=meeting_details,
            user_intent=user_intent,
        )

        # Get the appropriate service based on user intent
        service = collecting_info_node.get_schedule_service(state)

        # Act
        result = service.is_details_complete(meeting_details)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"


class TestUpdateStateMeetingDetails:
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
                    duration=30,
                ),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                ),
                "update empty state with complete details",
            ),
            # Partial update - only add missing fields
            (
                MeetingFindings(title="Team Standup", date_time="2024-01-15 10:00 AM"),
                MeetingFindings(participants=["john@example.com"], duration=30),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                ),
                "partial update adding missing fields",
            ),
            # Update existing fields
            (
                MeetingFindings(
                    title="Old Meeting",
                    date_time="2024-01-15 10:00 AM",
                    participants=["old@example.com"],
                    duration=60,
                ),
                MeetingFindings(title="New Meeting", participants=["new@example.com"]),
                MeetingFindings(
                    title="New Meeting",
                    date_time="2024-01-15 10:00 AM",
                    participants=["new@example.com"],
                    duration=60,
                ),
                "update existing fields keeping others unchanged",
            ),
            # None values should not update existing fields
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                ),
                MeetingFindings(
                    title=None, date_time=None, location="Conference Room A"
                ),
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                    location="Conference Room A",
                ),
                "none values do not overwrite existing fields",
            ),
        ],
    )
    def test_update_state_meeting_details(
        self,
        collecting_info_node,
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
        result_state = (
            collecting_info_node.meeting_service.update_state_meeting_details(
                new_meeting_details, state
            )
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

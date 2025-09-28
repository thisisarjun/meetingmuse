from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage

from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState


class TestMeetingDetailsService:
    """Test suite for MeetingDetailsService."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.mark.parametrize(
        "meeting_details,expected_result,test_description",
        [
            # Complete meeting details should return True
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com", "jane@example.com"],
                    duration=30,
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
                    duration=30,
                ),
                False,
                "missing title",
            ),
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=[],  # Empty participants list
                    duration=30,
                ),
                False,
                "empty participants list",
            ),
            (MeetingFindings(), False, "empty meeting details"),
        ],
    )
    def test_is_details_complete(
        self, meeting_service, meeting_details, expected_result, test_description
    ):
        """Test is_details_complete returns correct boolean based on meeting details completeness."""
        # Act
        result = meeting_service.is_details_complete(meeting_details)

        # Assert
        assert result == expected_result, f"Failed for case: {test_description}"

    @pytest.mark.parametrize(
        "meeting_details,expected_missing,test_description",
        [
            # Complete meeting details should return empty list
            (
                MeetingFindings(
                    title="Team Standup",
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                ),
                [],
                "complete meeting details",
            ),
            # Missing individual required fields
            (
                MeetingFindings(
                    title=None,
                    date_time="2024-01-15 10:00 AM",
                    participants=["john@example.com"],
                    duration=30,
                ),
                ["title"],
                "missing title only",
            ),
            (
                MeetingFindings(),
                ["title", "date_time", "participants", "duration"],
                "empty meeting details - all missing",
            ),
        ],
    )
    def test_get_missing_required_fields(
        self, meeting_service, meeting_details, expected_missing, test_description
    ):
        """Test get_missing_required_fields returns correct list of missing fields."""
        # Act
        result = meeting_service.get_missing_required_fields(meeting_details)

        # Assert
        assert set(result) == set(
            expected_missing
        ), f"Failed for case: {test_description}"

    def test_update_state_meeting_details(self, meeting_service):
        """Test update_state_meeting_details correctly updates state with new meeting details."""
        # Arrange
        initial_details = MeetingFindings(
            title="Old Meeting", date_time="2024-01-15 10:00 AM"
        )
        state = MeetingMuseBotState(messages=[], meeting_details=initial_details)
        new_details = MeetingFindings(
            title="New Meeting", participants=["john@example.com"]
        )

        # Act
        result_state = meeting_service.update_state_meeting_details(new_details, state)

        # Assert - result_state is actually a MeetingFindings object, not a state
        assert result_state.title == "New Meeting"
        assert (
            result_state.date_time == "2024-01-15 10:00 AM"
        )  # Should remain unchanged
        assert result_state.participants == ["john@example.com"]
        # result_state is now a MeetingFindings object, not the same state object

    def test_generate_completion_message(self, meeting_service):
        """Test generate_completion_message creates correct completion message."""
        # Arrange
        meeting_details = MeetingFindings(
            title="Team Standup",
            date_time="2024-01-15 10:00 AM",
            participants=["john@example.com", "jane@example.com"],
            duration=30,
            location="Conference Room A",
        )

        # Act
        result = meeting_service.generate_completion_message(meeting_details)

        # Assert
        expected = "Perfect! I'll schedule your meeting 'Team Standup' for 2024-01-15 10:00 AM with john@example.com, jane@example.com for 30 minutes at Conference Room A."
        assert result == expected

    def test_generate_completion_message_without_location(self, meeting_service):
        """Test generate_completion_message creates correct completion message without location."""
        # Arrange
        meeting_details = MeetingFindings(
            title="Team Standup",
            date_time="2024-01-15 10:00 AM",
            participants=["john@example.com"],
            duration=30,
        )

        # Act
        result = meeting_service.generate_completion_message(meeting_details)

        # Assert
        expected = "Perfect! I'll schedule your meeting 'Team Standup' for 2024-01-15 10:00 AM with john@example.com for 30 minutes."
        assert result == expected

    def test_get_missing_fields_via_prompt_success(self, meeting_service, mock_model):
        """Test get_missing_fields_via_prompt calls the chain correctly."""
        # Arrange
        state = MeetingMuseBotState(
            messages=[], meeting_details=MeetingFindings(title="Team Meeting")
        )
        mock_response = Mock()
        mock_response.response_message = "What time would you like the meeting?"

        with patch.object(meeting_service, "interactive_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_response

            # Act
            result = meeting_service.get_missing_fields_via_prompt(state)

            # Assert
            assert AIMessage(content=mock_response.response_message) == result
            mock_chain.invoke.assert_called_once()

    def test_get_missing_fields_via_prompt_error(self, meeting_service, mock_logger):
        """Test get_missing_fields_via_prompt handles errors correctly."""
        # Arrange
        state = MeetingMuseBotState(
            messages=[], meeting_details=MeetingFindings(title="Team Meeting")
        )

        with patch.object(meeting_service, "interactive_chain") as mock_chain:
            mock_chain.invoke.side_effect = Exception("LLM Error")

            # Act & Assert
            with pytest.raises(Exception, match="LLM Error"):
                meeting_service.get_missing_fields_via_prompt(state)

            mock_logger.error.assert_called_once_with(
                "Missing fields prompt error: LLM Error"
            )

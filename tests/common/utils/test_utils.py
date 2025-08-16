import pytest
from langchain_core.messages import AIMessage, HumanMessage

from common.utils import Utils
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState


class TestUtils:
    """Test suite for Utils class methods."""

    @pytest.fixture
    def empty_state(self):
        """Create a state with no messages."""
        return MeetingMuseBotState(messages=[], meeting_details=MeetingFindings())

    @pytest.fixture
    def state_with_human_message(self):
        """Create a state with only a human message."""
        return MeetingMuseBotState(
            messages=[HumanMessage(content="Hello, I need help")],
            meeting_details=MeetingFindings(),
        )

    @pytest.fixture
    def state_with_ai_message(self):
        """Create a state with only an AI message."""
        return MeetingMuseBotState(
            messages=[AIMessage(content="How can I help you?")],
            meeting_details=MeetingFindings(),
        )

    @pytest.fixture
    def state_with_mixed_messages(self):
        """Create a state with multiple mixed messages."""
        return MeetingMuseBotState(
            messages=[
                HumanMessage(content="First human message"),
                AIMessage(content="First AI response"),
                HumanMessage(content="Second human message"),
                AIMessage(content="Second AI response"),
            ],
            meeting_details=MeetingFindings(),
        )

    @pytest.fixture
    def state_ending_with_human(self):
        """Create a state ending with a human message."""
        return MeetingMuseBotState(
            messages=[
                AIMessage(content="AI message"),
                HumanMessage(content="Last human message"),
            ],
            meeting_details=MeetingFindings(),
        )

    @pytest.fixture
    def state_ending_with_ai(self):
        """Create a state ending with an AI message."""
        return MeetingMuseBotState(
            messages=[
                HumanMessage(content="Human message"),
                AIMessage(content="Last AI message"),
            ],
            meeting_details=MeetingFindings(),
        )


class TestIsLastMessageHuman(TestUtils):
    """Test suite for Utils.is_last_message_human method."""

    def test_is_last_message_human_with_human_last(self, state_ending_with_human):
        """Test returns True when last message is from human."""
        # Act
        result = Utils.is_last_message_human(state_ending_with_human)

        # Assert
        assert result is True

    def test_is_last_message_human_with_ai_last(self, state_ending_with_ai):
        """Test returns False when last message is from AI."""
        # Act
        result = Utils.is_last_message_human(state_ending_with_ai)

        # Assert
        assert result is False

    def test_is_last_message_human_with_single_human_message(
        self, state_with_human_message
    ):
        """Test returns True when only message is from human."""
        # Act
        result = Utils.is_last_message_human(state_with_human_message)

        # Assert
        assert result is True

    def test_is_last_message_human_with_single_ai_message(self, state_with_ai_message):
        """Test returns False when only message is from AI."""
        # Act
        result = Utils.is_last_message_human(state_with_ai_message)

        # Assert
        assert result is False

    def test_is_last_message_human_with_empty_messages(self, empty_state):
        """Test raises IndexError when no messages exist."""
        # Act & Assert
        with pytest.raises(IndexError):
            Utils.is_last_message_human(empty_state)


class TestIsLastMessageAI(TestUtils):
    """Test suite for Utils.is_last_message_ai method."""

    def test_is_last_message_ai_with_ai_last(self, state_ending_with_ai):
        """Test returns True when last message is from AI."""
        # Act
        result = Utils.is_last_message_ai(state_ending_with_ai)

        # Assert
        assert result is True

    def test_is_last_message_ai_with_human_last(self, state_ending_with_human):
        """Test returns False when last message is from human."""
        # Act
        result = Utils.is_last_message_ai(state_ending_with_human)

        # Assert
        assert result is False

    def test_is_last_message_ai_with_single_ai_message(self, state_with_ai_message):
        """Test returns True when only message is from AI."""
        # Act
        result = Utils.is_last_message_ai(state_with_ai_message)

        # Assert
        assert result is True

    def test_is_last_message_ai_with_single_human_message(
        self, state_with_human_message
    ):
        """Test returns False when only message is from human."""
        # Act
        result = Utils.is_last_message_ai(state_with_human_message)

        # Assert
        assert result is False

    def test_is_last_message_ai_with_empty_messages(self, empty_state):
        """Test raises IndexError when no messages exist."""
        # Act & Assert
        with pytest.raises(IndexError):
            Utils.is_last_message_ai(empty_state)


class TestGetLastMessage(TestUtils):
    """Test suite for Utils.get_last_message method."""

    def test_get_last_message_human_type(self, state_with_mixed_messages):
        """Test gets last human message when type is 'human'."""
        # Act
        result = Utils.get_last_message(state_with_mixed_messages, "human")

        # Assert
        assert result == "Second human message"

    def test_get_last_message_ai_type(self, state_with_mixed_messages):
        """Test gets last AI message when type is 'ai'."""
        # Act
        result = Utils.get_last_message(state_with_mixed_messages, "ai")

        # Assert
        assert result == "Second AI response"

    def test_get_last_message_human_type_only_ai_messages(self, state_with_ai_message):
        """Test returns None when searching for human message but only AI messages exist."""
        # Act
        result = Utils.get_last_message(state_with_ai_message, "human")

        # Assert
        assert result is None

    def test_get_last_message_ai_type_only_human_messages(
        self, state_with_human_message
    ):
        """Test returns None when searching for AI message but only human messages exist."""
        # Act
        result = Utils.get_last_message(state_with_human_message, "ai")

        # Assert
        assert result is None

    def test_get_last_message_single_human_message(self, state_with_human_message):
        """Test gets human message when only one human message exists."""
        # Act
        result = Utils.get_last_message(state_with_human_message, "human")

        # Assert
        assert result == "Hello, I need help"

    def test_get_last_message_single_ai_message(self, state_with_ai_message):
        """Test gets AI message when only one AI message exists."""
        # Act
        result = Utils.get_last_message(state_with_ai_message, "ai")

        # Assert
        assert result == "How can I help you?"

    def test_get_last_message_multiple_same_type(self):
        """Test gets the most recent message when multiple messages of same type exist."""
        # Arrange
        state = MeetingMuseBotState(
            messages=[
                HumanMessage(content="First human"),
                HumanMessage(content="Second human"),
                AIMessage(content="AI response"),
                HumanMessage(content="Third human"),
            ],
            meeting_details=MeetingFindings(),
        )

        # Act
        result = Utils.get_last_message(state, "human")

        # Assert
        assert result == "Third human"


class TestGetLastMessageFromEvents(TestUtils):
    """Test suite for Utils.get_last_message_from_events method."""

    def test_get_last_message_from_events_human_type(self):
        """Test gets last human message from events."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[HumanMessage(content="First human")],
                meeting_details=MeetingFindings(),
            ),
            "node2": MeetingMuseBotState(
                messages=[AIMessage(content="AI response")],
                meeting_details=MeetingFindings(),
            ),
            "node3": MeetingMuseBotState(
                messages=[HumanMessage(content="Last human")],
                meeting_details=MeetingFindings(),
            ),
        }

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        assert result == "Last human"

    def test_get_last_message_from_events_ai_type(self):
        """Test gets last AI message from events."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[AIMessage(content="First AI")],
                meeting_details=MeetingFindings(),
            ),
            "node2": MeetingMuseBotState(
                messages=[HumanMessage(content="Human message")],
                meeting_details=MeetingFindings(),
            ),
            "node3": MeetingMuseBotState(
                messages=[AIMessage(content="Last AI")],
                meeting_details=MeetingFindings(),
            ),
        }

        # Act
        result = Utils.get_last_message_from_events(events, "ai")

        # Assert
        assert result == "Last AI"

    def test_get_last_message_from_events_no_matching_type(self):
        """Test returns None when no messages of requested type exist."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[AIMessage(content="Only AI message")],
                meeting_details=MeetingFindings(),
            )
        }

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        assert result is None

    def test_get_last_message_from_events_empty_events(self):
        """Test returns None when events dict is empty."""
        # Arrange
        events = {}

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        assert result is None

    def test_get_last_message_from_events_empty_messages(self):
        """Test returns None when all states have empty message lists."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[], meeting_details=MeetingFindings()
            ),
            "node2": MeetingMuseBotState(
                messages=[], meeting_details=MeetingFindings()
            ),
        }

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        assert result is None

    def test_get_last_message_from_events_mixed_states(self):
        """Test handles mix of empty and non-empty message states."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[], meeting_details=MeetingFindings()
            ),
            "node2": MeetingMuseBotState(
                messages=[HumanMessage(content="Found message")],
                meeting_details=MeetingFindings(),
            ),
            "node3": MeetingMuseBotState(
                messages=[], meeting_details=MeetingFindings()
            ),
        }

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        assert result == "Found message"

    def test_get_last_message_from_events_multiple_messages_per_state(self):
        """Test gets the last message when states have multiple messages."""
        # Arrange
        events = {
            "node1": MeetingMuseBotState(
                messages=[
                    HumanMessage(content="First in node1"),
                    AIMessage(content="AI in node1"),
                    HumanMessage(content="Last in node1"),
                ],
                meeting_details=MeetingFindings(),
            ),
            "node2": MeetingMuseBotState(
                messages=[HumanMessage(content="Only in node2")],
                meeting_details=MeetingFindings(),
            ),
        }

        # Act
        result = Utils.get_last_message_from_events(events, "human")

        # Assert
        # Should get the last human message from the last processed state
        assert result in ["Last in node1", "Only in node2"]

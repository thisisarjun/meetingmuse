from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from common.logger import Logger
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.services.intent_classifier import IntentClassifier


class TestClassifyIntentNode:
    """Test suite for ClassifyIntentNode focusing on significant business logic."""

    @pytest.fixture
    def mock_intent_classifier(self):
        """Create a mock intent classifier for testing."""
        return Mock(spec=IntentClassifier)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def node(self, mock_intent_classifier, mock_logger):
        """Create a ClassifyIntentNode instance with mocked classifier."""
        return ClassifyIntentNode(mock_intent_classifier, mock_logger)

    def test_call_updates_state_with_classified_intent_and_step(
        self, node, mock_intent_classifier
    ):
        """
        Test the core workflow: classify intent and update state appropriately.

        This tests the main business logic of the node.
        """
        # Arrange
        mock_intent_classifier.classify.return_value = UserIntent.SCHEDULE_MEETING

        initial_state = MeetingMuseBotState(
            messages=[
                AIMessage(content="Hello! How can I help you?"),
                HumanMessage(content="I want to schedule a meeting"),
            ],
            user_intent=None,
            meeting_details=MeetingFindings(),
        )

        # Act
        result = node.node_action(initial_state)

        # Assert
        mock_intent_classifier.classify.assert_called_once_with(
            "I want to schedule a meeting"
        )
        assert result.user_intent == UserIntent.SCHEDULE_MEETING

        # Ensure other state fields are preserved
        assert len(result.messages) == 2
        assert result.meeting_details == MeetingFindings()

    def test_call_handles_conversation_with_multiple_human_messages(
        self, node, mock_intent_classifier
    ):
        """
        Test that the node correctly processes the last human message in a conversation.

        This tests realistic conversation scenarios where there are multiple exchanges.
        """
        # Arrange
        mock_intent_classifier.classify.return_value = UserIntent.CANCEL_MEETING

        state = MeetingMuseBotState(
            messages=[
                HumanMessage(content="Hello"),
                AIMessage(content="Hi! How can I help?"),
                HumanMessage(content="Actually, cancel my 3pm meeting"),
            ],
            user_intent=UserIntent.GENERAL_CHAT,  # Previous intent
            meeting_details=MeetingFindings(title="Old meeting"),
        )

        # Act
        result = node.node_action(state)

        # Assert
        mock_intent_classifier.classify.assert_called_once_with(
            "Actually, cancel my 3pm meeting"
        )
        assert result.user_intent == UserIntent.CANCEL_MEETING

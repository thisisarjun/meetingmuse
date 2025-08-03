from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage
from langgraph.types import Command

from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode


class TestHumanInterruptRetryNode:
    """Test suite for HumanInterruptRetryNode."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_logger = Mock()
        self.node = HumanInterruptRetryNode(logger=mock_logger)
        self.base_state = MeetingMuseBotState(
            messages=[],
            user_intent="schedule",
            meeting_details=MeetingFindings(
                title="Team standup", date_time="tomorrow at 2pm"
            ),
        )

    def test_node_name(self):
        """Test that the node returns the correct name."""
        assert self.node.node_name == NodeName.HUMAN_INTERRUPT_RETRY

    @patch("meetingmuse.nodes.human_interrupt_retry_node.interrupt")
    def test_retry_approval_true(self, mock_interrupt):
        """Test when user approves retry."""
        # Mock interrupt to return True (user chose retry)
        mock_interrupt.return_value = True

        # Execute node action
        result = self.node.node_action(self.base_state)

        # Verify interrupt was called with correct parameters
        mock_interrupt.assert_called_once_with(
            {
                "type": "operation_approval",
                "message": "Meeting scheduling failed. Would you like to retry?",
                "question": "Would you like to retry this operation?",
                "options": ["retry", "cancel"],
            }
        )

        mock_interrupt.assert_called_once_with(
            {
                "type": "operation_approval",
                "message": "Meeting scheduling failed. Would you like to retry?",
                "question": "Would you like to retry this operation?",
                "options": ["retry", "cancel"],
            }
        )

        # Verify result is Command to go to schedule_meeting
        assert isinstance(result, Command)
        assert result.goto == "schedule_meeting"

        # Verify retry message was added to state
        assert len(self.base_state.messages) == 1
        assert isinstance(self.base_state.messages[0], AIMessage)
        assert "retry" in self.base_state.messages[0].content.lower()
        assert "attempting again" in self.base_state.messages[0].content.lower()

    @patch("meetingmuse.nodes.human_interrupt_retry_node.interrupt")
    def test_retry_approval_false(self, mock_interrupt):
        """Test when user declines retry (cancels)."""
        # Mock interrupt to return False (user chose cancel)
        mock_interrupt.return_value = False

        # Execute node action
        result = self.node.node_action(self.base_state)

        # Verify interrupt was called with correct parameters
        mock_interrupt.assert_called_once_with(
            {
                "type": "operation_approval",
                "message": "Meeting scheduling failed. Would you like to retry?",
                "question": "Would you like to retry this operation?",
                "options": ["retry", "cancel"],
            }
        )

        mock_interrupt.assert_called_once_with(
            {
                "type": "operation_approval",
                "message": "Meeting scheduling failed. Would you like to retry?",
                "question": "Would you like to retry this operation?",
                "options": ["retry", "cancel"],
            }
        )

        # Verify result is Command to go to end
        assert isinstance(result, Command)
        assert result.goto == NodeName.END

        # Verify cancel message was added to state
        assert len(self.base_state.messages) == 1
        assert isinstance(self.base_state.messages[0], AIMessage)
        assert "cancel" in self.base_state.messages[0].content.lower()
        assert "operation ended" in self.base_state.messages[0].content.lower()

    @patch("meetingmuse.nodes.human_interrupt_retry_node.interrupt")
    def test_state_preservation(self, mock_interrupt):
        """Test that existing state is preserved during retry flow."""
        # State with existing messages
        state_with_history = MeetingMuseBotState(
            messages=[
                AIMessage(content="Previous interaction"),
                AIMessage(content="Another message"),
                AIMessage(content="Another message"),
            ],
            user_intent="schedule",
            meeting_details=MeetingFindings(
                title="Important meeting", participants=["alice@example.com"]
            ),
        )

        mock_interrupt.return_value = True

        # Execute node action
        self.node.node_action(state_with_history)

        self.node.node_action(state_with_history)

        # Verify existing messages are preserved and new retry message is added (called twice)
        assert len(state_with_history.messages) == 5  # 3 original + 2 retry messages
        assert state_with_history.messages[0].content == "Previous interaction"
        assert state_with_history.messages[1].content == "Another message"
        assert state_with_history.messages[2].content == "Another message"

        # Verify meeting details are preserved
        assert state_with_history.meeting_details.title == "Important meeting"
        assert "alice@example.com" in state_with_history.meeting_details.participants

        # Verify user intent is preserved
        assert state_with_history.user_intent == "schedule"

    @patch("meetingmuse.nodes.human_interrupt_retry_node.interrupt")
    def test_interrupt_parameters_structure(self, mock_interrupt):
        """Test that interrupt is called with the correct parameter structure."""
        mock_interrupt.return_value = True

        self.node.node_action(self.base_state)

        # Get the actual call arguments
        call_args = mock_interrupt.call_args[0][0]

        # Verify all required keys are present
        required_keys = ["type", "message", "question", "options"]
        for key in required_keys:
            assert key in call_args, f"Missing required key: {key}"

        # Verify types and values
        assert call_args["type"] == "operation_approval"
        assert isinstance(call_args["message"], str)
        assert isinstance(call_args["question"], str)
        assert isinstance(call_args["options"], list)
        assert call_args["options"] == ["retry", "cancel"]

    def test_inheritance(self):
        """Test that the node properly inherits from BaseNode."""
        from meetingmuse.nodes.base_node import BaseNode

        assert isinstance(self.node, BaseNode)

        # Verify required methods exist
        assert hasattr(self.node, "node_action")
        assert hasattr(self.node, "node_name")
        assert hasattr(self.node, "node_action")
        assert hasattr(self.node, "node_name")
        assert callable(self.node.node_action)

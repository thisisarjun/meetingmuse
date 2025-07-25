import pytest
from unittest.mock import patch, MagicMock
from langgraph.types import Command
from langchain_core.messages import AIMessage

from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.models.node import NodeName


class TestHumanInterruptRetryNode:
    """Test suite for HumanInterruptRetryNode."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.node = HumanInterruptRetryNode()
        self.base_state = MeetingMuseBotState(
            messages=[],
            user_intent="schedule",
            meeting_details={
                "title": "Team standup",
                "date_time": "tomorrow at 2pm"
            },
            operation_name="Meeting Scheduling"
        )
    
    def test_node_name(self):
        """Test that the node returns the correct name."""
        assert self.node.node_name == NodeName.HUMAN_INTERRUPT_RETRY
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_retry_approval_true(self, mock_interrupt):
        """Test when user approves retry."""
        # Mock interrupt to return True (user chose retry)
        mock_interrupt.return_value = True
        
        # Execute node action
        result = self.node.node_action(self.base_state)
        
        # Verify interrupt was called with correct parameters
        mock_interrupt.assert_called_once_with({
            "type": "operation_approval",
            "message": "Meeting Scheduling failed. Would you like to retry?",
            "question": "Would you like to retry this operation?",
            "operation": "Meeting Scheduling",
            "options": ["retry", "cancel"]
        })
        
        # Verify result is Command to go to schedule_meeting
        assert isinstance(result, Command)
        assert result.goto == "schedule_meeting"
        
        # Verify retry message was added to state
        assert len(self.base_state.messages) == 1
        assert isinstance(self.base_state.messages[0], AIMessage)
        assert "retry" in self.base_state.messages[0].content.lower()
        assert "attempting again" in self.base_state.messages[0].content.lower()
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_retry_approval_false(self, mock_interrupt):
        """Test when user declines retry (cancels)."""
        # Mock interrupt to return False (user chose cancel)
        mock_interrupt.return_value = False
        
        # Execute node action
        result = self.node.node_action(self.base_state)
        
        # Verify interrupt was called with correct parameters
        mock_interrupt.assert_called_once_with({
            "type": "operation_approval",
            "message": "Meeting Scheduling failed. Would you like to retry?",
            "question": "Would you like to retry this operation?",
            "operation": "Meeting Scheduling",
            "options": ["retry", "cancel"]
        })
        
        # Verify result is Command to go to end
        assert isinstance(result, Command)
        assert result.goto == "end"
        
        # Verify cancel message was added to state
        assert len(self.base_state.messages) == 1
        assert isinstance(self.base_state.messages[0], AIMessage)
        assert "cancel" in self.base_state.messages[0].content.lower()
        assert "operation ended" in self.base_state.messages[0].content.lower()
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_custom_operation_name(self, mock_interrupt):
        """Test with custom operation name."""
        # Set custom operation name
        custom_state = MeetingMuseBotState(
            messages=[],
            user_intent="schedule",
            meeting_details={},
            operation_name="Calendar Sync"
        )
        
        mock_interrupt.return_value = True
        
        # Execute node action
        result = self.node.node_action(custom_state)
        
        # Verify interrupt was called with custom operation name
        mock_interrupt.assert_called_once_with({
            "type": "operation_approval",
            "message": "Calendar Sync failed. Would you like to retry?",
            "question": "Would you like to retry this operation?",
            "operation": "Calendar Sync",
            "options": ["retry", "cancel"]
        })
        
        # Verify message contains custom operation name
        assert "Calendar Sync" in custom_state.messages[0].content
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_default_operation_name(self, mock_interrupt):
        """Test with default operation name when none provided."""
        # State without operation_name
        state_without_op = MeetingMuseBotState(
            messages=[],
            user_intent="schedule",
            meeting_details={}
        )
        
        mock_interrupt.return_value = False
        
        # Execute node action
        result = self.node.node_action(state_without_op)
        
        # Verify interrupt was called with default operation name
        mock_interrupt.assert_called_once_with({
            "type": "operation_approval",
            "message": "Meeting Scheduling failed. Would you like to retry?",
            "question": "Would you like to retry this operation?",
            "operation": "Meeting Scheduling",
            "options": ["retry", "cancel"]
        })
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_state_preservation(self, mock_interrupt):
        """Test that existing state is preserved during retry flow."""
        # State with existing messages
        state_with_history = MeetingMuseBotState(
            messages=[
                AIMessage(content="Previous interaction"),
                AIMessage(content="Another message")
            ],
            user_intent="schedule",
            meeting_details={
                "title": "Important meeting",
                "participants": ["alice@example.com"]
            },
            operation_name="Meeting Scheduling"
        )
        
        mock_interrupt.return_value = True
        
        # Execute node action
        result = self.node.node_action(state_with_history)
        
        # Verify existing messages are preserved
        assert len(state_with_history.messages) == 3
        assert state_with_history.messages[0].content == "Previous interaction"
        assert state_with_history.messages[1].content == "Another message"
        
        # Verify meeting details are preserved
        assert state_with_history.meeting_details["title"] == "Important meeting"
        assert "alice@example.com" in state_with_history.meeting_details["participants"]
        
        # Verify user intent is preserved
        assert state_with_history.user_intent == "schedule"
    
    @patch('meetingmuse.nodes.human_interrupt_retry_node.interrupt')
    def test_interrupt_parameters_structure(self, mock_interrupt):
        """Test that interrupt is called with the correct parameter structure."""
        mock_interrupt.return_value = True
        
        self.node.node_action(self.base_state)
        
        # Get the actual call arguments
        call_args = mock_interrupt.call_args[0][0]
        
        # Verify all required keys are present
        required_keys = ["type", "message", "question", "operation", "options"]
        for key in required_keys:
            assert key in call_args, f"Missing required key: {key}"
        
        # Verify types and values
        assert call_args["type"] == "operation_approval"
        assert isinstance(call_args["message"], str)
        assert isinstance(call_args["question"], str)
        assert isinstance(call_args["operation"], str)
        assert isinstance(call_args["options"], list)
        assert call_args["options"] == ["retry", "cancel"]
    
    def test_inheritance(self):
        """Test that the node properly inherits from BaseNode."""
        from meetingmuse.nodes.base_node import BaseNode
        assert isinstance(self.node, BaseNode)
        
        # Verify required methods exist
        assert hasattr(self.node, 'node_action')
        assert hasattr(self.node, 'node_name')
        assert callable(self.node.node_action)

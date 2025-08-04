"""
Tests for Message Processor
Unit tests for LangGraph message processing
"""
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from langchain_core.messages import AIMessage  # noqa: E402

from server.langgraph.message_processor import LangGraphMessageProcessor  # noqa: E402


class TestLangGraphMessageProcessor:
    """Test suite for LangGraph Message Processor"""

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    def test_processor_initialization(self, mock_factory_class):
        """Test that the processor initializes correctly"""
        mock_graph = Mock()
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        assert processor.graph == mock_graph
        mock_factory_class.get_graph.assert_called_once()

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    @pytest.mark.asyncio
    async def test_process_user_message_success(self, mock_factory_class):
        """Test successful message processing"""
        # Setup mocks
        mock_graph = Mock()
        mock_ai_message = AIMessage(content="AI response content")

        mock_result = {"messages": [mock_ai_message]}

        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        # Test message processing
        result = await processor.process_user_message("Hello", "client123")

        assert result == "AI response content"
        mock_graph.ainvoke.assert_called_once()

        # Check the call arguments
        call_args = mock_graph.ainvoke.call_args
        input_data = call_args[0][0]  # First positional argument
        config = call_args.kwargs["config"]  # Keyword argument
        assert config == {"configurable": {"thread_id": "client123"}}
        assert "messages" in input_data

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    @pytest.mark.asyncio
    async def test_process_user_message_error(self, mock_factory_class):
        """Test error handling in message processing"""
        # Setup mocks to raise an exception
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Processing failed"))
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        # Test error handling
        result = await processor.process_user_message("Hello", "client123")

        assert "error processing your request" in result.lower()

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    @pytest.mark.asyncio
    async def test_handle_interrupts_with_pending_interrupt(self, mock_factory_class):
        """Test handling interrupts when there are pending interrupts"""
        # Setup mocks
        mock_graph = Mock()
        mock_state = Mock()
        mock_state.next = ["some_node"]

        mock_graph.get_state.return_value = mock_state
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        # Test interrupt handling
        result = await processor.handle_interrupts("client123")

        assert result is not None
        assert result["waiting_for_input"] is True
        assert result["next_step"] == "some_node"
        assert "prompt" in result

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    @pytest.mark.asyncio
    async def test_handle_interrupts_no_interrupts(self, mock_factory_class):
        """Test handling interrupts when there are no pending interrupts"""
        # Setup mocks
        mock_graph = Mock()
        mock_state = Mock()
        mock_state.next = None

        mock_graph.get_state.return_value = mock_state
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        # Test interrupt handling
        result = await processor.handle_interrupts("client123")

        assert result is None

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    @pytest.mark.asyncio
    async def test_get_conversation_state_with_conversation(self, mock_factory_class):
        """Test getting conversation state when conversation exists"""
        # Setup mocks
        mock_graph = Mock()
        mock_state = Mock()
        mock_state.values = {
            "messages": ["msg1", "msg2"],
            "user_intent": "schedule_meeting",
            "meeting_details": {"title": "Test Meeting"},
        }
        mock_state.next = None

        mock_graph.get_state.return_value = mock_state
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        # Test getting conversation state
        result = await processor.get_conversation_state("client123")

        assert result is not None
        assert result["has_conversation"] is True
        assert result["message_count"] == 2
        assert result["user_intent"] == "schedule_meeting"
        assert result["is_interrupted"] is False

    @patch("meetingmuse_server.langgraph.message_processor.LangGraphSingletonFactory")
    def test_is_ready(self, mock_factory_class):
        """Test the is_ready method"""
        mock_graph = Mock()
        mock_factory_instance = Mock()
        mock_factory_instance.is_initialized.return_value = True
        mock_factory_class.return_value = mock_factory_instance
        mock_factory_class.get_graph.return_value = mock_graph

        processor = LangGraphMessageProcessor()

        assert processor.is_ready() is True


if __name__ == "__main__":
    pytest.main([__file__])

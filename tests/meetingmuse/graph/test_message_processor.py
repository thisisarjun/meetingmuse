"""
Test suite for MessageProcessor.process_user_message method.
"""

import pytest
from langchain_core.messages import HumanMessage

from meetingmuse.graph.message_processor import MessageProcessor


class TestMessageProcessorProcessUserMessage:
    """Test suite for MessageProcessor.process_user_message method."""

    @pytest.fixture
    def message_processor(self, mock_graph, mock_logger):
        """Create a MessageProcessor instance with mocked dependencies."""
        return MessageProcessor(mock_graph, mock_logger)

    @pytest.mark.asyncio
    async def test_process_user_message_success_with_ai_response(
        self, message_processor, mock_graph, sample_meeting_muse_state
    ):
        """Test successful message processing with AI response."""
        # Arrange
        user_content = "I need to schedule a meeting for tomorrow"
        client_id = "test_client_123"
        expected_response = "I'd be happy to help you schedule a meeting. Could you please provide more details?"

        # Mock the graph.ainvoke to return our test state
        mock_graph.ainvoke.return_value = sample_meeting_muse_state.model_dump()

        # Act
        result = await message_processor.process_user_message(user_content, client_id)

        # Assert
        assert result == expected_response
        mock_graph.ainvoke.assert_called_once()
        mock_graph.ainvoke.assert_called_with(
            {"messages": [HumanMessage(content=user_content)]},
            config={"configurable": {"thread_id": client_id}},
        )

    @pytest.mark.asyncio
    async def test_process_user_message_no_ai_message_in_state(
        self, message_processor, mock_graph, state_with_only_human_message, mock_logger
    ):
        """Test when state contains no AI message."""
        # Arrange
        user_content = "Hello"
        client_id = "test_client_123"
        expected_fallback = (
            "I'm having trouble processing your request. Please try again."
        )

        mock_graph.ainvoke.return_value = state_with_only_human_message.model_dump()

        # Act
        result = await message_processor.process_user_message(user_content, client_id)

        # Assert
        assert result == expected_fallback
        mock_logger.warning.assert_called_once_with(
            f"No messages in result for client {client_id}"
        )

    @pytest.mark.asyncio
    async def test_process_user_message_empty_state(
        self, message_processor, mock_graph, empty_meeting_muse_state, mock_logger
    ):
        """Test when state is empty."""
        # Arrange
        user_content = "Hello"
        client_id = "test_client_123"
        expected_fallback = (
            "I'm having trouble processing your request. Please try again."
        )

        mock_graph.ainvoke.return_value = empty_meeting_muse_state.model_dump()

        # Act
        result = await message_processor.process_user_message(user_content, client_id)

        # Assert
        assert result == expected_fallback
        mock_logger.warning.assert_called_once_with(
            f"No messages in result for client {client_id}"
        )

    @pytest.mark.asyncio
    async def test_process_user_message_graph_not_initialized(self, mock_logger):
        """Test when graph is not initialized."""
        # Arrange
        message_processor = MessageProcessor(None, mock_logger)
        user_content = "Hello"
        client_id = "test_client_123"
        expected_error_response = (
            "I encountered an error processing your request. Please try again."
        )

        # Act
        result = await message_processor.process_user_message(user_content, client_id)

        # Assert
        assert result == expected_error_response
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_user_message_graph_ainvoke_raises_exception(
        self, message_processor, mock_graph, mock_logger
    ):
        """Test when graph.ainvoke raises an exception."""
        # Arrange
        user_content = "Hello"
        client_id = "test_client_123"
        expected_error_response = (
            "I encountered an error processing your request. Please try again."
        )

        mock_graph.ainvoke.side_effect = Exception("Graph processing failed")

        # Act
        result = await message_processor.process_user_message(user_content, client_id)

        # Assert
        assert result == expected_error_response
        mock_logger.error.assert_called_once_with(
            f"Error processing message for client {client_id}: Graph processing failed"
        )

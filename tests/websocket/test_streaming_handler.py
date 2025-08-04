"""
Tests for Streaming Handler
Unit tests for real-time response streaming
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from server.handlers.streaming_handler import StreamingHandler


class TestStreamingHandler:
    """Test suite for Streaming Handler"""
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    def test_handler_initialization(self, mock_factory_class):
        """Test that the handler initializes correctly"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        assert handler.factory == mock_factory
        assert handler.graph == mock_graph
        mock_factory.get_graph_instance.assert_called_once()
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_stream_response_success(self, mock_factory_class):
        """Test successful response streaming"""
        # Setup mocks
        mock_factory = Mock()
        mock_graph = Mock()
        
        # Mock the async generator for astream
        async def mock_astream(*args, **kwargs):
            yield {"messages": [Mock(content="First response")]}
            yield {"collecting_info": {"some": "data"}}
        
        mock_graph.astream = mock_astream
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        # Test streaming
        input_data = {"messages": ["test message"]}
        updates = []
        async for update in handler.stream_response(input_data, "client123"):
            updates.append(update)
        
        assert len(updates) >= 1
        # Check that we got some processing updates
        assert any(update.get("type") in ["ai_response", "processing_step"] for update in updates)
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_stream_response_error(self, mock_factory_class):
        """Test error handling in response streaming"""
        # Setup mocks to raise an exception
        mock_factory = Mock()
        mock_graph = Mock()
        mock_graph.astream = AsyncMock(side_effect=Exception("Streaming failed"))
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        # Test error handling
        input_data = {"messages": ["test message"]}
        updates = []
        async for update in handler.stream_response(input_data, "client123"):
            updates.append(update)
        
        assert len(updates) == 1
        assert updates[0]["type"] == "error"
        assert "client123" in updates[0]["client_id"]
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_process_chunk_ai_message(self, mock_factory_class):
        """Test processing chunk with AI message"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        # Mock AI message
        mock_ai_message = Mock()
        mock_ai_message.content = "AI response content"
        mock_ai_message.__class__.__name__ = "AIMessage"
        
        # Mock the isinstance check
        with patch('meetingmuse_server.streaming_handler.AIMessage') as mock_ai_class:
            # Make isinstance return True for our mock
            def isinstance_side_effect(obj, cls):
                return obj is mock_ai_message and cls is mock_ai_class
            
            with patch('builtins.isinstance', side_effect=isinstance_side_effect):
                chunk = {"messages": [mock_ai_message]}
                result = await handler._process_chunk(chunk, "client123")
        
        assert result is not None
        assert result["type"] == "ai_response"
        assert result["content"] == "AI response content"
        assert result["client_id"] == "client123"
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_process_chunk_node_execution(self, mock_factory_class):
        """Test processing chunk with node execution data"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        chunk = {"collecting_info": {"some": "data"}}
        result = await handler._process_chunk(chunk, "client123")
        
        assert result is not None
        assert result["type"] == "processing_step"
        assert result["step"] == "collecting_info"
        assert "Processing through collecting info" in result["content"]
        assert result["client_id"] == "client123"
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_send_processing_notification(self, mock_factory_class):
        """Test sending processing notifications"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        result = await handler.send_processing_notification("intent_classification", "client123")
        
        assert result["type"] == "processing_step"
        assert result["step"] == "intent_classification"
        assert result["content"] == "Analyzing your request..."
        assert result["client_id"] == "client123"
        assert "timestamp" in result
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    @pytest.mark.asyncio
    async def test_create_interrupt_notification(self, mock_factory_class):
        """Test creating interrupt notifications"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        interrupt_info = {
            "prompt": "Please provide meeting duration",
            "next_step": "schedule_meeting"
        }
        
        result = await handler.create_interrupt_notification(interrupt_info, "client123")
        
        assert result["type"] == "waiting_for_input"
        assert result["content"] == "Please provide meeting duration"
        assert result["next_step"] == "schedule_meeting"
        assert result["client_id"] == "client123" 
        assert "metadata" in result
        assert "suggestions" in result["metadata"]
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')
    def test_get_input_suggestions_meeting(self, mock_factory_class):
        """Test getting input suggestions for meeting-related interrupts"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        interrupt_info = {"next_step": "schedule_meeting"}
        suggestions = handler._get_input_suggestions(interrupt_info)
        
        assert len(suggestions) > 0
        assert any("2 PM" in suggestion for suggestion in suggestions)
    
    @patch('meetingmuse_server.handlers.streaming_handler.LangGraphFactory')  
    def test_is_ready(self, mock_factory_class):
        """Test the is_ready method"""
        mock_factory = Mock()
        mock_graph = Mock()
        mock_factory.get_graph_instance.return_value = mock_graph
        mock_factory_class.return_value = mock_factory
        
        handler = StreamingHandler()
        
        assert handler.is_ready() is True


if __name__ == "__main__":
    pytest.main([__file__])

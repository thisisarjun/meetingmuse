"""
Tests for Conversation Manager
Unit tests for conversation state management and recovery
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from server.services.conversation_manager import ConversationManager


class TestConversationManager:
    """Test suite for Conversation Manager"""
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    def test_manager_initialization(self, mock_processor_class):
        """Test that the manager initializes correctly"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        assert manager.message_processor == mock_processor
        assert manager.active_conversations == {}
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_initialize_conversation(self, mock_processor_class):
        """Test conversation initialization"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Test initializing a new conversation
        result = await manager.initialize_conversation("client123")
        
        assert result is True
        assert "client123" in manager.active_conversations
        assert manager.active_conversations["client123"]["status"] == "active"
        assert "started_at" in manager.active_conversations["client123"]
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_handle_reconnection_with_existing_conversation(self, mock_processor_class):
        """Test handling reconnection when conversation exists"""
        mock_processor = Mock()
        mock_processor.get_conversation_state = AsyncMock(return_value={
            "has_conversation": True,
            "message_count": 5,
            "user_intent": "schedule_meeting",
            "meeting_details": {"title": "Team Meeting"},
            "is_interrupted": False
        })
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Test reconnection handling
        result = await manager.handle_reconnection("client123")
        
        assert result is not None
        assert result["conversation_resumed"] is True
        assert "summary" in result
        assert result["message_count"] == 5
        assert result["user_intent"] == "schedule_meeting"
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_handle_reconnection_no_existing_conversation(self, mock_processor_class):
        """Test handling reconnection when no conversation exists"""
        mock_processor = Mock()
        mock_processor.get_conversation_state = AsyncMock(return_value={
            "has_conversation": False
        })
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Test reconnection handling
        result = await manager.handle_reconnection("client123")
        
        assert result is not None
        assert result["conversation_resumed"] is False
        assert result["summary"] == "Starting a new conversation"
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_generate_conversation_summary_meeting_with_time(self, mock_processor_class):
        """Test conversation summary generation for meeting with time"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        state_info = {
            "user_intent": "schedule_meeting",
            "meeting_details": {
                "title": "Team Standup",
                "date_time": "tomorrow at 2 PM"
            },
            "message_count": 3
        }
        
        summary = await manager._generate_conversation_summary("client123", state_info)
        
        assert "Team Standup" in summary
        assert "tomorrow at 2 PM" in summary
        assert "3 messages" in summary
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_update_conversation_activity(self, mock_processor_class):
        """Test updating conversation activity"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Initialize conversation first
        await manager.initialize_conversation("client123")
        initial_count = manager.active_conversations["client123"]["message_count"]
        
        # Update activity
        await manager.update_conversation_activity("client123")
        
        # Check that message count increased
        assert manager.active_conversations["client123"]["message_count"] == initial_count + 1
        assert "last_activity" in manager.active_conversations["client123"]
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    @pytest.mark.asyncio
    async def test_end_conversation(self, mock_processor_class):
        """Test ending a conversation"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Initialize and then end conversation
        await manager.initialize_conversation("client123")
        await manager.end_conversation("client123")
        
        assert manager.active_conversations["client123"]["status"] == "ended"
        assert "ended_at" in manager.active_conversations["client123"]
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    def test_get_active_conversation_count(self, mock_processor_class):
        """Test getting active conversation count"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Add some conversations with different statuses
        manager.active_conversations = {
            "client1": {"status": "active"},
            "client2": {"status": "ended"},
            "client3": {"status": "active"}
        }
        
        count = manager.get_active_conversation_count()
        assert count == 2
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    def test_list_active_conversations(self, mock_processor_class):
        """Test listing active conversations"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        # Add some conversations with different statuses
        manager.active_conversations = {
            "client1": {"status": "active"},
            "client2": {"status": "ended"},
            "client3": {"status": "active"}
        }
        
        active_list = manager.list_active_conversations()
        assert len(active_list) == 2
        assert "client1" in active_list
        assert "client3" in active_list
        assert "client2" not in active_list
    
    @patch('meetingmuse_server.services.conversation_manager.LangGraphMessageProcessor')
    def test_is_processor_ready(self, mock_processor_class):
        """Test checking if processor is ready"""
        mock_processor = Mock()
        mock_processor.is_ready.return_value = True
        mock_processor_class.return_value = mock_processor
        
        manager = ConversationManager()
        
        assert manager.is_processor_ready() is True
        mock_processor.is_ready.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])

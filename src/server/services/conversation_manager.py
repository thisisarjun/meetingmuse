"""
Conversation Manager for WebSocket Server
Handles conversation state and recovery for WebSocket connections
"""
from typing import Any, Optional, Dict, List
import logging
from datetime import datetime

from ..langgraph.message_processor import LangGraphMessageProcessor

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state and recovery for WebSocket connections"""
    
    def __init__(self):
        self.message_processor = LangGraphMessageProcessor()
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
    
    async def initialize_conversation(self, client_id: str) -> bool:
        """
        Initialize conversation state for a new client
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if client_id not in self.active_conversations:
                self.active_conversations[client_id] = {
                    "started_at": datetime.now().isoformat(),
                    "last_activity": datetime.now().isoformat(),
                    "message_count": 0,
                    "status": "active"
                }
                logger.info(f"Initialized conversation for client {client_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize conversation for client {client_id}: {str(e)}")
            return False
    
    async def handle_reconnection(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Handle conversation recovery after reconnection
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with conversation recovery information
        """
        try:
            # Get current conversation state from LangGraph
            state_info = await self.message_processor.get_conversation_state(client_id)
            
            if state_info and state_info.get("has_conversation"):
                # Generate conversation summary
                summary = await self._generate_conversation_summary(client_id, state_info)
                
                recovery_info = {
                    "conversation_resumed": True,
                    "summary": summary,
                    "message_count": state_info.get("message_count", 0),
                    "user_intent": state_info.get("user_intent"),
                    "is_interrupted": state_info.get("is_interrupted", False),
                    "meeting_details": state_info.get("meeting_details", {})
                }
                
                # Update conversation metadata
                if client_id in self.active_conversations:
                    self.active_conversations[client_id]["last_activity"] = datetime.now().isoformat()
                    self.active_conversations[client_id]["status"] = "resumed"
                
                logger.info(f"Conversation recovered for client {client_id}")
                return recovery_info
            
            # No existing conversation found
            return {
                "conversation_resumed": False,
                "summary": "Starting a new conversation"
            }
            
        except Exception as e:
            logger.error(f"Error handling reconnection for client {client_id}: {str(e)}")
            return None
    
    async def _generate_conversation_summary(self, client_id: str, state_info: Dict[str, Any]) -> str:
        """
        Generate a summary of the current conversation
        
        Args:
            client_id: Client identifier
            state_info: Current conversation state information
            
        Returns:
            Human-readable conversation summary
        """
        try:
            user_intent = state_info.get("user_intent")
            meeting_details = state_info.get("meeting_details", {})
            message_count = state_info.get("message_count", 0)
            
            if user_intent == "schedule_meeting":
                # Create meeting-specific summary
                title = meeting_details.get("title", "a meeting")
                date_time = meeting_details.get("date_time")
                
                if date_time:
                    return f"We were scheduling {title} for {date_time}. We've exchanged {message_count} messages so far."
                else:
                    return f"We were working on scheduling {title}. We've exchanged {message_count} messages so far."
            
            elif user_intent:
                return f"We were discussing {user_intent.replace('_', ' ')}. We've exchanged {message_count} messages so far."
            
            else:
                return f"We've been chatting. We've exchanged {message_count} messages so far."
                
        except Exception as e:
            logger.error(f"Error generating conversation summary for client {client_id}: {str(e)}")
            return "Continuing our previous conversation."
    
    async def update_conversation_activity(self, client_id: str) -> None:
        """
        Update conversation activity timestamp
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.active_conversations:
            self.active_conversations[client_id]["last_activity"] = datetime.now().isoformat()
            self.active_conversations[client_id]["message_count"] += 1
    
    async def end_conversation(self, client_id: str) -> None:
        """
        Mark conversation as ended and cleanup
        
        Args:
            client_id: Client identifier
        """
        try:
            if client_id in self.active_conversations:
                self.active_conversations[client_id]["status"] = "ended"
                self.active_conversations[client_id]["ended_at"] = datetime.now().isoformat()
                
                # Optional: Remove old conversations after some time
                # For now, we'll keep them for potential analysis
                
                logger.info(f"Conversation ended for client {client_id}")
                
        except Exception as e:
            logger.error(f"Error ending conversation for client {client_id}: {str(e)}")
    
    def get_conversation_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation metadata
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with conversation metadata
        """
        return self.active_conversations.get(client_id)
    
    def get_active_conversation_count(self) -> int:
        """Get count of active conversations"""
        return len([
            conv for conv in self.active_conversations.values() 
            if conv.get("status") == "active"
        ])
    
    def list_active_conversations(self) -> List[str]:
        """Get list of active conversation client IDs"""
        return [
            client_id for client_id, conv in self.active_conversations.items()
            if conv.get("status") == "active"
        ]
    
    def is_processor_ready(self) -> bool:
        """Check if the message processor is ready"""
        return self.message_processor.is_ready()

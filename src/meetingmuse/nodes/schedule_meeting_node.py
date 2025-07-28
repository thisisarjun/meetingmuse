from typing import Literal
from langgraph.types import Command
from langgraph.graph import END
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from langchain_core.messages import AIMessage
import random

class ScheduleMeetingNode(BaseNode):
    """
    Node that handles API calls for scheduling meetings.
    If the user intent is 'schedule', this node will attempt to schedule the meeting.
    On success, goes to END. On failure, goes to human interrupt retry node.
    """
    
    def __init__(self, model=None, logger=None):
        """Initialize the node with optional model and logger."""
        self.model = model
        self.logger = logger
    
    def node_action(self, state: MeetingMuseBotState) -> Command[Literal["__end__", "human_interrupt_retry"]]:
        if self.logger:
            self.logger.info("Starting meeting scheduling process")
        
        print(f"DEBUG: Current state: {state}")
        
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            message = "No scheduling action needed for this intent."
            if self.logger:
                self.logger.info(message)
            state.messages.append(AIMessage(content=message))
            return Command(goto=END)
        
        # Simulate API call to schedule meeting
        # TODO: Replace with actual API call logic
        try:
            # Check if we have sufficient meeting details
            # TODO: Can be removed if dedicated validation node precedes this node
            if not self._has_sufficient_details(state):
                message = "Insufficient meeting details for scheduling."
                if self.logger:
                    self.logger.warning(message)
                state.messages.append(AIMessage(content=message))
                return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)
            
            # Simulate API call (30% success rate for demo purposes)
            if random.random() < 0.3:
                # Success case
                meeting_id = f"MTG_{random.randint(1000, 9999)}"
                success_message = (
                    f"✅ Meeting scheduled successfully! "
                    f"Meeting ID: {meeting_id}. "
                    f"Title: {state.meeting_details.title or 'Meeting'}, "
                    f"Time: {state.meeting_details.date_time or 'TBD'}"
                )
                if self.logger:
                    self.logger.info(f"Meeting scheduled successfully with ID: {meeting_id}")
                state.messages.append(AIMessage(content=success_message))
                return Command(goto=END)
            else:
                # Failure case
                error_msg = "Calendar service temporarily unavailable. Please try again."
                if self.logger:
                    self.logger.error(f"Meeting scheduling failed: {error_msg}")
                state.messages.append(AIMessage(content=f"❌ Failed to schedule meeting: {error_msg}"))
                return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)
                
        except Exception as e:
            # Exception handling
            error_msg = f"Unexpected error during scheduling: {str(e)}"
            if self.logger:
                self.logger.error(f"Exception in scheduling: {error_msg}")
            state.messages.append(AIMessage(content=f"❌ {error_msg}"))
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)
    
    def _has_sufficient_details(self, state: MeetingMuseBotState) -> bool:
        """Check if we have enough details to schedule a meeting."""
        details = state.meeting_details
        return all([
            details.title is not None,
            details.date_time is not None,
            details.participants is not None,
            details.duration is not None
        ])
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

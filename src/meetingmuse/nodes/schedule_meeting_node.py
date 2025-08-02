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
    
    def __init__(self, model, logger):
        """Initialize the node with optional model and logger."""
        self.model = model
        self.logger = logger
    
    def node_action(self, state: MeetingMuseBotState) -> Command[Literal[NodeName.END, NodeName.HUMAN_INTERRUPT_RETRY]]:
        self.logger.info("Starting meeting scheduling process")
        
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            message = "No scheduling action needed for this intent."
            self.logger.info(message)
            state.messages.append(AIMessage(content=message))
            return Command(goto=END)
        
        # Simulate API call to schedule meeting
        # TODO: Replace with actual API call logic
        try:
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
                self.logger.info(f"Meeting scheduled successfully with ID: {meeting_id}")
                state.messages.append(AIMessage(content=success_message))
                return Command(goto=END)
            else:
                # Failure case
                error_msg = "Calendar service temporarily unavailable. Please try again."
                self.logger.error(f"Meeting scheduling failed: {error_msg}")
                state.messages.append(AIMessage(content=f"❌ Failed to schedule meeting: {error_msg}"))
                return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)
                
        except Exception as e:
            # Exception handling
            error_msg = f"Unexpected error during scheduling: {str(e)}"
            self.logger.error(f"Exception in scheduling: {error_msg}")
            state.messages.append(AIMessage(content=f"❌ {error_msg}"))
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

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
    
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            state.messages.append(AIMessage(content="No scheduling action needed for this intent."))
            state.api_call_status = "skipped"
            return state
        
        # Simulate API call to schedule meeting
        # TODO: Replace with actual API call logic
        try:
            # Check if we have sufficient meeting details
            # TODO: Can be removed if dedicated validation node precedes this node
            if not self._has_sufficient_details(state):
                state.messages.append(AIMessage(content="Insufficient meeting details for scheduling."))
                state.api_call_status = "insufficient_details"
                return state
            
            # Simulate API call (70% success rate for demo purposes)
            if random.random() < 0.7:
                # Success case
                meeting_id = f"MTG_{random.randint(1000, 9999)}"
                success_message = (
                    f"✅ Meeting scheduled successfully! "
                    f"Meeting ID: {meeting_id}. "
                    f"Title: {state.meeting_details.title or 'Meeting'}, "
                    f"Time: {state.meeting_details.date_time or 'TBD'}"
                )
                state.messages.append(AIMessage(content=success_message))
                state.api_call_status = "success"
            else:
                # Failure case
                error_msg = "Calendar service temporarily unavailable. Please try again."
                state.messages.append(AIMessage(content=f"❌ Failed to schedule meeting: {error_msg}"))
                state.api_call_status = "failed"
                state.api_error_message = error_msg
                
        except Exception as e:
            # Exception handling
            error_msg = f"Unexpected error during scheduling: {str(e)}"
            state.messages.append(AIMessage(content=f"❌ {error_msg}"))
            state.api_call_status = "failed"
            state.api_error_message = error_msg
        
        return state
    
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

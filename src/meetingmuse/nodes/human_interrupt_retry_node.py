from typing import Literal
from langgraph.types import interrupt, Command
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from langchain_core.messages import HumanMessage, AIMessage

class HumanInterruptRetryNode(BaseNode):
    """
    Dedicated node for handling human interruption and retry decisions using LangGraph's native interrupt pattern.
    This node uses interrupt() and Command() for proper human-in-the-loop workflow.
    """
    
    def node_action(self, state: MeetingMuseBotState) -> Command[Literal["schedule_meeting", "end"]]:
        # Get operation details from state
        operation_name = state.get("operation_name", "Meeting Scheduling")
        
        # Use LangGraph's interrupt() for human decision
        approval = interrupt({
            "type": "operation_approval",
            "message": f"{operation_name} failed. Would you like to retry?",
            "question": "Would you like to retry this operation?",
            "operation": operation_name,
            "options": ["retry", "cancel"]
        })
        
        if approval:
            # User chose to retry - go back to API call
            state.messages.append(AIMessage(content=f"User chose to retry {operation_name}. Attempting again..."))
            return Command(goto="schedule_meeting")  # Use the correct node name from NodeName.SCHEDULE_MEETING
        else:
            # User chose to cancel - end the operation
            state.messages.append(AIMessage(content=f"User chose to cancel {operation_name}. Operation ended."))
            return Command(goto="end")
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_INTERRUPT_RETRY

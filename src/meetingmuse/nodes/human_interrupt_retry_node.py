from typing import Literal
from langgraph.types import interrupt, Command
from langgraph.graph import END
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from langchain_core.messages import HumanMessage, AIMessage

class HumanInterruptRetryNode(BaseNode):
    """
    Dedicated node for handling human interruption and retry decisions using LangGraph's native interrupt pattern.
    This node uses interrupt() and Command() for proper human-in-the-loop workflow.
    """
    
    def __init__(self, model=None, logger=None):
        """Initialize the node with optional model and logger."""
        self.model = model
        self.logger = logger
    
    def node_action(self, state: MeetingMuseBotState) -> Command[Literal["schedule_meeting", "__end__"]]:
        # Get operation details from state
        operation_name = getattr(state, "operation_name", "Meeting Scheduling")
        
        if self.logger:
            self.logger.info(f"Human interrupt requested for operation: {operation_name}")
        
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
            retry_message = f"User chose to retry {operation_name}. Attempting again..."
            if self.logger:
                self.logger.info(f"User chose to retry operation: {operation_name}")
            state.messages.append(AIMessage(content=retry_message))
            return Command(goto=NodeName.SCHEDULE_MEETING)
        else:
            # User chose to cancel - end the operation
            cancel_message = f"User chose to cancel {operation_name}. Operation ended."
            if self.logger:
                self.logger.info(f"User chose to cancel operation: {operation_name}")
            state.messages.append(AIMessage(content=cancel_message))
            return Command(goto=END)
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_INTERRUPT_RETRY

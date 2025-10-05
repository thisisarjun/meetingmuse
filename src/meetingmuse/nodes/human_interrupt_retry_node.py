from typing import Any

from langchain_core.messages import AIMessage
from langgraph.types import Command, interrupt

from common.decorators import log_node_entry
from meetingmuse.models.interrupts import InterruptOperationApproval
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import SyncNode


class HumanInterruptRetryNode(SyncNode):
    """
    Dedicated node for handling human interruption and retry decisions using LangGraph's native interrupt pattern.
    This node uses interrupt() and Command() for proper human-in-the-loop workflow.
    """

    @log_node_entry(NodeName.HUMAN_INTERRUPT_RETRY)
    def node_action(self, state: MeetingMuseBotState) -> Command[Any]:
        self.logger.info("Human interrupt requested")

        # Use LangGraph's interrupt() for human decision

        options = ["retry", "cancel"]
        interrupt_info = InterruptOperationApproval(
            message="Meeting scheduling failed.",
            question="Would you like to retry this operation?",
        )
        approval: str = interrupt(interrupt_info)

        if approval not in options:
            self.logger.error(f"Invalid choice, please choose {'/ '.join(options)}")
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)

        if approval == "retry":
            # User chose to retry - go back to API call
            retry_message: str = "User chose to retry. Attempting again..."

            self.logger.info("User chose to retry operation")
            state.messages.append(AIMessage(content=retry_message))
            return Command(
                goto=NodeName.SCHEDULE_MEETING, update={"messages": state.messages}
            )
        # User chose to cancel - end the operation
        cancel_message: str = "I understand. I apologize for the technical issue with our calendar system. The meeting request has been canceled. Please feel free to try again later or let me know if there's anything else I can help you with."  # pylint: disable=line-too-long

        self.logger.info("User chose to cancel operation")
        state.messages.append(AIMessage(content=cancel_message))
        return Command(goto=NodeName.END, update={"messages": state.messages})

    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_INTERRUPT_RETRY

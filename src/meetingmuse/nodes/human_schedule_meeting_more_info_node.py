from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from meetingmuse.models.interrupts import InterruptInfo, InterruptType
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.utils.decorators.log_decorator import log_node_entry
from meetingmuse.utils.logger import Logger


class HumanScheduleMeetingMoreInfoNode(BaseNode):
    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)

    @log_node_entry(NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO)
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        interrupt_info = InterruptInfo(
            type=InterruptType.SEEK_MORE_INFO,
            message="Need more information to schedule the meeting",
            question=state.operation_status.ai_prompt_input or "",
        )
        human_input: Any = interrupt(interrupt_info)
        if not isinstance(human_input, str):
            raise ValueError("Human input must be a string")

        self.logger.info(f"Received human input: {human_input}")

        # Check if user provided any input
        if not human_input or human_input.strip() == "":
            self.logger.info("No input provided, asking again")
            # For now, we'll continue with the state instead of returning Command
            # TODO: Implement proper retry logic
            return state

        # Parse human input and update meeting details
        state.messages.append(HumanMessage(content=human_input))
        state.operation_status.ai_prompt_input = None
        self.logger.info("Human input processed, continuing to collecting_info node")
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO

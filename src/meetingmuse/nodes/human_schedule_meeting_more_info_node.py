
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt, Command

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.utils.logger import Logger


class HumanScheduleMeetingMoreInfoNode(BaseNode):
    def __init__(self, logger: Logger):
        self.logger = logger


    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        
        self.logger.info(f"Entering {self.node_name} node with current state: {state.meeting_details}")        
        human_input = interrupt(state.ai_prompt_input)


        self.logger.info(f"Received human input: {human_input}")
        
        # Check if user provided any input
        if not human_input or human_input.strip() == "":
            self.logger.info("No input provided, asking again")
            # Return to same node to ask again
            return Command(goto=self.node_name)
        
        # Parse human input and update meeting details
        state.messages.append(HumanMessage(content=human_input))
        state.ai_prompt_input = None
        self.logger.info("Human input processed, continuing to collecting_info node")
        return state

    
    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO
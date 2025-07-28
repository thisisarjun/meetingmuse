
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt, Command

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.utils.logger import Logger


class HumanScheduleMeetingMoreInfoNode(BaseNode):
    def __init__(self, logger: Logger, meeting_service: MeetingDetailsService):
        self.meeting_service = meeting_service
        self.logger = logger

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        
        self.logger.info(f"current state: {state.meeting_details}")        

        # Check if we already have missing fields to avoid re-generating the prompt
        missing_fields = self.meeting_service.get_missing_required_fields(state.meeting_details)
        
        if not missing_fields:
            # No missing fields, continue to collecting info
            self.logger.info("All required fields are present, continuing to collecting_info")
            return Command(goto="collecting_info")
        
        try:
            response = self.meeting_service.invoke_missing_fields_prompt(state).content
        except Exception as e:
            self.logger.error(f"Missing fields prompt error: {e}")
            response = "I need some more information to schedule your meeting. Could you provide the missing details?"
        
        # Interrupt and wait for human input
        human_input = interrupt(response)
        self.logger.info(f"Received human input: {human_input}")
        
        # Check if user provided any input
        if not human_input or human_input.strip() == "":
            self.logger.info("No input provided, asking again")
            # Return to same node to ask again
            return Command(goto=self.node_name)
        
        # Parse human input and update meeting details
        state.messages.append(HumanMessage(content=human_input))
        self.logger.info("Human input processed, continuing to collecting_info node")
        return Command(goto="collecting_info")

    
    @property
    def node_name(self) -> NodeName:
        return NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO
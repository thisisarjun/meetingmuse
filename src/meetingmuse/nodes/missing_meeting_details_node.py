from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.utils.logger import Logger
from meetingmuse.models.node import NodeName
from langgraph.types import Command, interrupt


class PromptMissingMeetingDetailsNode(BaseNode):
    def __init__(self, logger: Logger, meeting_service: MeetingDetailsService):
          self.meeting_service = meeting_service
          self.logger = logger

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        self.logger.info(f"Entering {self.node_name} node...")

        missing_fields = self.meeting_service.get_missing_required_fields(state.meeting_details)

        if not missing_fields:
            # NOTE: this is an error in graph, should not happen
            self.logger.error(f"Meeting details are complete, but node {self.node_name} was called")
<!-- TODO: Route to meeting scheduler -->
            return Command(goto=NodeName.END)

        try:
            response = self.meeting_service.invoke_missing_fields_prompt(state).content
        except Exception as e:
            response = "I need some more information, could you provide all the details? I need the following information: " + ", ".join(missing_fields)

        state.ai_prompt_input = response
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.PROMPT_MISSING_MEETING_DETAILS
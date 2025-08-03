from typing import List

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.utils.decorators.log_decorator import log_node_entry
from meetingmuse.utils.logger import Logger


class PromptMissingMeetingDetailsNode(BaseNode):
    meeting_service: MeetingDetailsService

    def __init__(self, meeting_service: MeetingDetailsService, logger: Logger) -> None:
        super().__init__(logger)
        self.meeting_service = meeting_service

    def get_next_node(self, state: MeetingMuseBotState) -> NodeName:
        if not state.operation_status.ai_prompt_input:
            return NodeName.END
        return NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO

    @log_node_entry(NodeName.PROMPT_MISSING_MEETING_DETAILS)
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        missing_fields: List[str] = self.meeting_service.get_missing_required_fields(
            state.meeting_details
        )

        if not missing_fields:
            # NOTE: this is an error in graph, should not happen!
            self.logger.error(
                f"Meeting details are complete, but node {self.node_name} was called"
            )
            return state

        try:
            prompt_response = self.meeting_service.invoke_missing_fields_prompt(state)
            # Handle both string and complex content types

            if hasattr(prompt_response, "content"):
                content = prompt_response.content
                if isinstance(content, str):
                    response = content
                else:
                    response = str(content)
            else:
                response = str(prompt_response)
        except Exception:  # pylint: disable=broad-exception-caught
            response = (
                "I need some more information, could you provide all the details? I need the following information: "
                + ", ".join(missing_fields)
            )

        state.operation_status.ai_prompt_input = response
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.PROMPT_MISSING_MEETING_DETAILS

from typing import List

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import SyncNode
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.reminder_details_service import ReminderDetailsService


class PromptMissingMeetingDetailsNode(SyncNode):
    schedule_service: MeetingDetailsService | ReminderDetailsService

    def __init__(
        self,
        meeting_service: MeetingDetailsService,
        reminder_service: ReminderDetailsService,
        logger: Logger,
    ) -> None:
        super().__init__(logger)
        self.meeting_service = meeting_service
        self.reminder_service = reminder_service

    def set_schedule_service(self, state: MeetingMuseBotState) -> None:
        self.schedule_service = (
            self.meeting_service
            if state.user_intent == UserIntent.SCHEDULE_MEETING
            else self.reminder_service
        )

    def get_next_node(self, state: MeetingMuseBotState) -> NodeName:
        if not state.operation_status.ai_prompt_input:
            return NodeName.END
        return NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO

    @log_node_entry(NodeName.PROMPT_MISSING_MEETING_DETAILS)
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        self.set_schedule_service(state)
        missing_fields: List[str] = self.schedule_service.get_missing_required_fields(
            state.meeting_details
        )

        if not missing_fields:
            # NOTE: this is an error in graph, should not happen!
            self.logger.error(
                f"Meeting details are complete, but node {self.node_name} was called"
            )
            return state

        try:
            prompt_response = self.schedule_service.get_missing_fields_via_prompt(state)
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

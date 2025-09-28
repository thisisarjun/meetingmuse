from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.graph.graph_utils.utils import Utils
from meetingmuse.llm_models.hugging_face import BaseLlmModel
from meetingmuse.models.graph import MessageType
from meetingmuse.models.meeting import InteractiveMeetingResponse, MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.prompts.schedule_meeting_collecting_info_prompt import (
    INTERACTIVE_MEETING_COLLECTION_PROMPT,
)
from meetingmuse.services.meeting_details_service import MeetingDetailsService


class CollectingInfoNode(BaseNode):
    """
    Collecting Info node specific for scheduling a meeting.
    This node is responsible for collecting information from the user.
    It is used to collect the meeting details from the user.
    """

    model: BaseLlmModel
    parser: PydanticOutputParser[InteractiveMeetingResponse]
    prompt: ChatPromptTemplate
    chain: Runnable[Dict[str, Any], InteractiveMeetingResponse]
    meeting_service: MeetingDetailsService

    def __init__(self, model: BaseLlmModel, logger: Logger) -> None:
        super().__init__(logger)
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=InteractiveMeetingResponse)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTERACTIVE_MEETING_COLLECTION_PROMPT),
            ]
        )
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.meeting_service = MeetingDetailsService(model, self.logger)

    @log_node_entry(NodeName.COLLECTING_INFO)
    def get_next_node_name(self, state: MeetingMuseBotState) -> NodeName:
        self.logger.info(f"Getting next node name: {state.meeting_details}")
        if state.meeting_details and self.meeting_service.is_meeting_details_complete(
            state.meeting_details
        ):
            self.logger.info(
                "Meeting details are complete, returning to Schedule Meeting Node"
            )
            return NodeName.SCHEDULE_MEETING
        self.logger.info(
            "Meeting details are not complete, returning to COLLECTING_INFO"
        )
        return NodeName.PROMPT_MISSING_MEETING_DETAILS

    def complete_state(
        self, meeting_details: MeetingFindings, state: MeetingMuseBotState
    ) -> MeetingMuseBotState:
        """Complete the state with the missing required fields"""
        response: str = self.meeting_service.generate_completion_message(
            meeting_details
        )
        state.messages.append(AIMessage(content=response))
        return state

    def invoke_extraction_prompt(
        self,
        meeting_details: MeetingFindings,
        missing_required: List[str],
        user_input: str,
    ) -> InteractiveMeetingResponse:
        """Invoke the extraction prompt to get the missing required fields"""
        prompt = self.chain.invoke(
            {
                "user_message": user_input,
                "current_details": meeting_details.model_dump(),
                "missing_fields": ", ".join(missing_required)
                if missing_required
                else "none",
                "todays_date": datetime.now().strftime("%Y-%m-%d"),
                "todays_day_name": datetime.now().strftime("%A"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )
        if not isinstance(prompt, InteractiveMeetingResponse):
            raise ValueError(f"Expected InteractiveMeetingResponse, got {type(prompt)}")
        return prompt

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        self.logger.info(
            f"Entering {self.node_name} node with current state: {state.meeting_details}"
        )

        last_human_message: Optional[str] = Utils.get_last_message(
            state, MessageType.HUMAN
        )

        if not last_human_message:
            return state

        meeting_details: MeetingFindings = state.meeting_details or MeetingFindings()
        self.logger.info(f"Meeting details: {meeting_details}")
        missing_required: List[str] = self.meeting_service.get_missing_required_fields(
            meeting_details
        )

        if self.meeting_service.is_meeting_details_complete(meeting_details):
            return self.complete_state(meeting_details, state)

        try:
            interactive_response: InteractiveMeetingResponse = (
                self.invoke_extraction_prompt(
                    meeting_details, missing_required, last_human_message
                )
            )
            new_meeting_details = interactive_response.extracted_data
            response_message = interactive_response.response_message
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(f"Parsing error: {e}")
            # Fallback: keep existing details and generate fallback response
            new_meeting_details = meeting_details
            response_message = "I need some more information to schedule your meeting. Could you provide the missing details?"

        # Update only non None fields
        updated_meeting_details = self.meeting_service.update_state_meeting_details(
            new_meeting_details, state
        )
        state.meeting_details = updated_meeting_details

        self.logger.info(f"Updated meeting details: {state.meeting_details}")

        state.messages.append(AIMessage(content=response_message))
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.COLLECTING_INFO

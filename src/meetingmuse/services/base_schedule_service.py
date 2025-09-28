from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from common.logger import Logger
from meetingmuse.llm_models.base import BaseLlmModel
from meetingmuse.models.meeting import InteractiveMeetingResponse, MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState


class BaseScheduleService(ABC):
    model: BaseLlmModel
    logger: Logger
    interactive_prompt: ChatPromptTemplate
    parser: PydanticOutputParser[InteractiveMeetingResponse]
    interactive_chain: Runnable[Dict[str, Any], InteractiveMeetingResponse]
    interactive_prompt_template: str

    def __init__(
        self, model: BaseLlmModel, logger: Logger, interactive_prompt_template: str
    ) -> None:
        self.interactive_prompt_template = interactive_prompt_template
        self.model = model
        self.logger = logger
        self.parser = PydanticOutputParser(pydantic_object=InteractiveMeetingResponse)
        self.interactive_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.interactive_prompt_template),
            ]
        )
        self.interactive_chain = (
            self.interactive_prompt | self.model.chat_model | self.parser
        )

    @abstractmethod
    def is_details_complete(self, details: MeetingFindings) -> bool:
        pass

    @abstractmethod
    def get_missing_required_fields(self, details: MeetingFindings) -> List[str]:
        pass

    @abstractmethod
    def generate_completion_message(self, details: MeetingFindings) -> str:
        pass

    def invoke_extraction_prompt(
        self,
        details: MeetingFindings,
        missing_required: List[str],
        user_input: str = "",
    ) -> InteractiveMeetingResponse:
        response: InteractiveMeetingResponse = self.interactive_chain.invoke(
            {
                "user_message": user_input,  # Empty message for pure response generation
                "current_details": details.model_dump(),
                "missing_fields": ", ".join(missing_required)
                if missing_required
                else "none",
                "todays_datetime": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "todays_day_name": datetime.now().strftime("%A"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )
        return response

    def get_missing_fields_via_prompt(self, state: MeetingMuseBotState) -> BaseMessage:
        """Generate a response message asking for missing fields using interactive prompt"""
        try:
            missing_required = self.get_missing_required_fields(state.meeting_details)
            response: InteractiveMeetingResponse = self.invoke_extraction_prompt(
                state.meeting_details, missing_required
            )
            # Create BaseMessage with the response content

            return AIMessage(content=response.response_message)
        except Exception as e:
            self.logger.error(f"Missing fields prompt error: {e}")
            raise

    def update_state_meeting_details(
        self, details: MeetingFindings, state: MeetingMuseBotState
    ) -> MeetingFindings:
        """Update the meeting details with new information"""
        # Create a new MeetingFindings object with updated values
        current = state.meeting_details
        updated_data = {}

        for key, value in details.model_dump().items():
            if value is not None:
                updated_data[key] = value
            else:
                # Keep existing value if new value is None
                updated_data[key] = getattr(current, key)

        return MeetingFindings(**updated_data)

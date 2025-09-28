from datetime import datetime
from typing import Any, Dict, List

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import BaseLlmModel
from meetingmuse.models.meeting import InteractiveMeetingResponse, MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.prompts.schedule_meeting_collecting_info_prompt import (
    INTERACTIVE_MEETING_COLLECTION_PROMPT,
)


class MeetingDetailsService:
    """Service for handling meeting details validation and prompts"""

    model: BaseLlmModel
    logger: Logger
    interactive_prompt: ChatPromptTemplate
    parser: PydanticOutputParser[InteractiveMeetingResponse]
    interactive_chain: Runnable[Dict[str, Any], InteractiveMeetingResponse]

    def __init__(self, model: BaseLlmModel, logger: Logger) -> None:
        self.model = model
        self.logger = logger
        self.parser = PydanticOutputParser(pydantic_object=InteractiveMeetingResponse)
        self.interactive_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTERACTIVE_MEETING_COLLECTION_PROMPT),
            ]
        )
        self.interactive_chain = (
            self.interactive_prompt | self.model.chat_model | self.parser
        )

    def is_meeting_details_complete(self, meeting_details: MeetingFindings) -> bool:
        """Check if all required fields are present (title, date_time, participants, duration)"""
        return all(
            [
                meeting_details.title is not None,
                meeting_details.date_time is not None,
                meeting_details.participants is not None
                and len(meeting_details.participants) > 0,
                meeting_details.duration is not None,
            ]
        )

    def get_missing_required_fields(
        self, meeting_details: MeetingFindings
    ) -> List[str]:
        """Get missing required fields (title, date_time, participants, duration)"""
        missing: List[str] = []
        if not meeting_details.title:
            missing.append("title")
        if not meeting_details.date_time:
            missing.append("date_time")
        if not meeting_details.participants or len(meeting_details.participants) == 0:
            missing.append("participants")
        if not meeting_details.duration:
            missing.append("duration")
        return missing

    def invoke_missing_fields_prompt(self, state: MeetingMuseBotState) -> BaseMessage:
        """Generate a response message asking for missing fields using interactive prompt"""
        try:
            missing_required = self.get_missing_required_fields(state.meeting_details)
            response: InteractiveMeetingResponse = self.interactive_chain.invoke(
                {
                    "user_message": "",  # Empty message for pure response generation
                    "current_details": state.meeting_details.model_dump(),
                    "missing_fields": ", ".join(missing_required)
                    if missing_required
                    else "none",
                    "todays_date": datetime.now().strftime("%Y-%m-%d"),
                    "todays_day_name": datetime.now().strftime("%A"),
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )
            # Create BaseMessage with the response content
            from langchain_core.messages import AIMessage

            return AIMessage(content=response.response_message)
        except Exception as e:
            self.logger.error(f"Missing fields prompt error: {e}")
            raise

    def update_state_meeting_details(
        self, meeting_details: MeetingFindings, state: MeetingMuseBotState
    ) -> MeetingFindings:
        """Update the meeting details with new information"""
        # Create a new MeetingFindings object with updated values
        current = state.meeting_details
        updated_data = {}

        for key, value in meeting_details.model_dump().items():
            if value is not None:
                updated_data[key] = value
            else:
                # Keep existing value if new value is None
                updated_data[key] = getattr(current, key)

        return MeetingFindings(**updated_data)

    def generate_completion_message(self, meeting_details: MeetingFindings) -> str:
        """Generate a completion message when all meeting details are collected"""
        # Ensure participants is not None before joining
        participants_str: str = (
            ", ".join(meeting_details.participants)
            if meeting_details.participants
            else "unknown participants"
        )

        # Format duration with "minutes" text
        duration_str: str = (
            f"{meeting_details.duration} minutes"
            if meeting_details.duration is not None
            else "unknown duration"
        )

        response: str = (
            f"Perfect! I'll schedule your meeting '{meeting_details.title}' "
            f"for {meeting_details.date_time} with {participants_str} "
            f"for {duration_str}"
        )
        if meeting_details.location:
            response += f" at {meeting_details.location}"
        response += "."
        return response

    def parse_human_response(
        self, human_input: str, current_details: MeetingFindings
    ) -> MeetingFindings:
        """Parse human input and update meeting details"""
        # TODO: Implement proper parsing logic using LLM
        # For now, basic implementation that assumes human input is the meeting title
        updated_details: MeetingFindings = MeetingFindings(
            title=current_details.title or human_input,
            participants=current_details.participants,
            date_time=current_details.date_time,
            duration=current_details.duration,
            location=current_details.location,
        )
        return updated_details

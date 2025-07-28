from langchain_core.prompts import ChatPromptTemplate
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.prompts.missing_fields_prompt import MISSING_FIELDS_PROMPT
from meetingmuse.utils.logger import Logger


class MeetingDetailsService:
    """Service for handling meeting details validation and prompts"""
    
    def __init__(self, model: HuggingFaceModel, logger: Logger):
        self.model = model
        self.logger = logger
        self.missing_fields_prompt = ChatPromptTemplate.from_messages([
            ("system", MISSING_FIELDS_PROMPT),
        ])
        self.missing_fields_chain = self.missing_fields_prompt | self.model.chat_model

    def is_meeting_details_complete(self, meeting_details: MeetingFindings) -> bool:
        """Check if all required fields are present (title, date_time, participants, duration)"""
        return all([
            meeting_details.title is not None,
            meeting_details.date_time is not None,
            meeting_details.participants is not None and len(meeting_details.participants) > 0,
            meeting_details.duration is not None
        ])

    def get_missing_required_fields(self, meeting_details: MeetingFindings) -> list[str]:
        """Get missing required fields (title, date_time, participants, duration)"""
        missing = []
        if not meeting_details.title:
            missing.append("title")
        if not meeting_details.date_time:
            missing.append("date_time")
        if not meeting_details.participants or len(meeting_details.participants) == 0:
            missing.append("participants")
        if not meeting_details.duration:
            missing.append("duration")
        return missing

    def invoke_missing_fields_prompt(self, state: MeetingMuseBotState) -> str:
        """Invoke the missing fields prompt to get the missing required fields"""
        try:
            return self.missing_fields_chain.invoke({
                "current_details": state.meeting_details.model_dump(),
                "missing_required": self.get_missing_required_fields(state.meeting_details)
            })
        except Exception as e:
            self.logger.error(f"Missing fields prompt error: {e}")
            raise

    def update_state_meeting_details(self, meeting_details: MeetingFindings, state: MeetingMuseBotState) -> MeetingMuseBotState:
        """Update the state with the new meeting details"""
        for key, value in meeting_details.model_dump().items():
            if value is not None:
                setattr(state.meeting_details, key, value)
        return state

    def generate_completion_message(self, meeting_details: MeetingFindings) -> str:
        """Generate a completion message when all meeting details are collected"""
        response = f"Perfect! I'll schedule your meeting '{meeting_details.title}' " \
                  f"for {meeting_details.date_time} with {', '.join(meeting_details.participants)} " \
                  f"for {meeting_details.duration}"
        if meeting_details.location:
            response += f" at {meeting_details.location}"
        response += "."
        return response

    def parse_human_response(self, human_input: str, current_details: MeetingFindings) -> MeetingFindings:
        """Parse human input and update meeting details"""
        # TODO: Implement proper parsing logic using LLM
        # For now, basic implementation that assumes human input is the meeting title
        updated_details = MeetingFindings(
            title=current_details.title or human_input,
            participants=current_details.participants,
            date_time=current_details.date_time,
            duration=current_details.duration,
            location=current_details.location
        )
        return updated_details 
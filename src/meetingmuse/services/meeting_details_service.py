from typing import List

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import BaseLlmModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.services.base_schedule_service import BaseScheduleService


class MeetingDetailsService(BaseScheduleService):
    """Service for handling meeting details validation and prompts"""

    def __init__(
        self, model: BaseLlmModel, logger: Logger, interactive_prompt_template: str
    ) -> None:
        super().__init__(model, logger, interactive_prompt_template)

    def is_details_complete(self, meeting_details: MeetingFindings) -> bool:
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

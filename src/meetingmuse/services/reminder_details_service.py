from typing import List

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import BaseLlmModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.services.base_schedule_service import BaseScheduleService


class ReminderDetailsService(BaseScheduleService):
    """Service for handling reminder details validation and prompts"""

    def __init__(
        self, model: BaseLlmModel, logger: Logger, interactive_prompt_template: str
    ) -> None:
        super().__init__(model, logger, interactive_prompt_template)

    def is_details_complete(self, reminder_details: MeetingFindings) -> bool:
        """Check if all required fields are present for reminder (title as topic, date_time)"""
        return all(
            [
                reminder_details.title is not None,
                reminder_details.date_time is not None,
            ]
        )

    def get_missing_required_fields(
        self, reminder_details: MeetingFindings
    ) -> List[str]:
        """Get missing required fields for reminder (title as topic, date_time)"""
        missing: List[str] = []
        if not reminder_details.title:
            missing.append("title")  # Using title field as topic for reminders
        if not reminder_details.date_time:
            missing.append("date_time")
        return missing

    def generate_completion_message(self, reminder_details: MeetingFindings) -> str:
        """Generate a completion message when all reminder details are collected"""
        response: str = (
            f"Perfect! I'll set a reminder for '{reminder_details.title}' "
            f"on {reminder_details.date_time}."
        )
        return response

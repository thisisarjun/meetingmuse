from typing import List

from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.services.base_schedule_service import BaseScheduleService


class MeetingDetailsService(BaseScheduleService):
    """Service for handling meeting details validation and prompts"""

    def is_details_complete(self, details: MeetingFindings) -> bool:
        """Check if all required fields are present (title, date_time, participants, duration)"""
        return all(
            [
                details.title is not None,
                details.date_time is not None,
                details.participants is not None and len(details.participants) > 0,
                details.duration is not None,
            ]
        )

    def get_missing_required_fields(self, details: MeetingFindings) -> List[str]:
        """Get missing required fields (title, date_time, participants, duration)"""
        missing: List[str] = []
        if not details.title:
            missing.append("title")
        if not details.date_time:
            missing.append("date_time")
        if not details.participants or len(details.participants) == 0:
            missing.append("participants")
        if not details.duration:
            missing.append("duration")
        return missing

    def generate_completion_message(self, details: MeetingFindings) -> str:
        """Generate a completion message when all meeting details are collected"""
        # Ensure participants is not None before joining
        participants_str: str = (
            ", ".join(details.participants)
            if details.participants
            else "unknown participants"
        )

        # Format duration with "minutes" text
        duration_str: str = (
            f"{details.duration} minutes"
            if details.duration is not None
            else "unknown duration"
        )

        response: str = (
            f"Perfect! I'll schedule your meeting '{details.title}' "
            f"for {details.date_time} with {participants_str} "
            f"for {duration_str}"
        )
        if details.location:
            response += f" at {details.location}"
        response += "."
        return response

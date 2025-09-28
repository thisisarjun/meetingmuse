from typing import Any, List, Optional, TypedDict

from pydantic import BaseModel


class AttendeeDict(TypedDict):
    """Type definition for calendar event attendee."""

    email: str


class CalendarEventDict(TypedDict):
    """Type definition for Google Calendar event payload."""

    summary: str
    location: str
    description: str
    start: dict[str, str]
    end: dict[str, str]
    attendees: list[AttendeeDict]
    reminders: dict[str, Any]


class MeetingFindings(BaseModel):
    """Simple Pydantic model for meeting scheduling findings"""

    title: Optional[str] = None
    participants: Optional[List[str]] = None
    date_time: Optional[str] = None
    duration: Optional[int] = None
    location: Optional[str] = None


class InteractiveMeetingResponse(BaseModel):
    """Pydantic model for interactive meeting collection response"""

    extracted_data: MeetingFindings
    response_message: str


class CalendarEventDetails(BaseModel):
    """Pydantic model for calendar event creation response"""

    event_id: str
    event_link: Optional[str] = None
    start_time: str
    end_time: str

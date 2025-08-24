from typing import List, Optional

from pydantic import BaseModel


class MeetingFindings(BaseModel):
    """Simple Pydantic model for meeting scheduling findings"""

    title: Optional[str] = None
    participants: Optional[List[str]] = None
    date_time: Optional[str] = None
    durationInMns: Optional[int] = None
    location: Optional[str] = None


class CalendarEventDetails(BaseModel):
    """Pydantic model for calendar event creation response"""

    event_id: str
    event_link: Optional[str] = None
    start_time: str
    end_time: str

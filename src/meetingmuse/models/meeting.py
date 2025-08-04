from typing import List, Optional

from pydantic import BaseModel


class MeetingFindings(BaseModel):
    """Simple Pydantic model for meeting scheduling findings"""

    title: Optional[str] = None
    participants: Optional[List[str]] = None
    date_time: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None

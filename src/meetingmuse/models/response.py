"""Structured response models for AI messages to provide better UX."""

from enum import Enum
from typing import Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field


class ResponseType(str, Enum):
    """Types of responses for different UI rendering."""

    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    AUTH_ERROR = "auth_error"


class LinkData(BaseModel):
    """Represents a clickable link in the response."""

    url: str = Field(..., description="The URL to link to")
    text: str = Field(..., description="Display text for the link")
    external: bool = Field(default=True, description="Whether link opens in new tab")


class TextElement(BaseModel):
    """Represents a text element with optional formatting."""

    text: str = Field(..., description="The text content")
    bold: bool = Field(default=False, description="Whether text should be bold")


class MeetingEventData(BaseModel):
    """Meeting event details for successful scheduling."""

    event_id: str = Field(..., description="Calendar event ID")
    title: str = Field(..., description="Meeting title")
    start_time: str = Field(..., description="Meeting start time")
    end_time: str = Field(..., description="Meeting end time")
    location: Optional[str] = Field(None, description="Meeting location")
    participants: List[str] = Field(
        default_factory=list, description="Meeting participants"
    )
    calendar_link: Optional[LinkData] = Field(
        None, description="Link to calendar event"
    )


class StructuredMessage(BaseModel):
    """Base structured message model."""

    type: ResponseType = Field(..., description="Type of response for UI rendering")
    title: Optional[str] = Field(None, description="Optional title for the message")
    content: Sequence[Union[str, TextElement, LinkData]] = Field(
        default_factory=list, description="Structured content elements"
    )
    metadata: Dict[str, Union[str, int, bool]] = Field(
        default_factory=dict, description="Additional metadata for UI rendering"
    )


class MeetingSuccessResponse(StructuredMessage):
    """Response for successful meeting scheduling."""

    type: ResponseType = Field(default=ResponseType.SUCCESS)
    meeting_data: MeetingEventData = Field(..., description="Meeting event details")

    @classmethod
    def create(cls, meeting_data: MeetingEventData) -> "MeetingSuccessResponse":
        """Create a MeetingSuccessResponse with properly formatted content."""
        content: List[Union[str, TextElement, LinkData]] = [
            TextElement(text="Meeting scheduled successfully!", bold=True),
            f"Event ID: {meeting_data.event_id}",
            f"Title: {meeting_data.title}",
            f"Time: {meeting_data.start_time} - {meeting_data.end_time}",
        ]

        if meeting_data.location:
            content.append(f"Location: {meeting_data.location}")

        if meeting_data.participants:
            content.append(f"Participants: {', '.join(meeting_data.participants)}")

        if meeting_data.calendar_link:
            content.append(meeting_data.calendar_link)

        return cls(
            title="Success",
            content=content,
            metadata={"theme": "success"},
            meeting_data=meeting_data,
        )


class ErrorResponse(StructuredMessage):
    """Response for error cases."""

    type: ResponseType = Field(default=ResponseType.ERROR)
    error_code: Optional[str] = Field(None, description="Error code for debugging")

    @classmethod
    def create(
        cls,
        message: str,
        error_type: ResponseType = ResponseType.ERROR,
        error_code: Optional[str] = None,
    ) -> "ErrorResponse":
        """Create an ErrorResponse with properly formatted content."""
        theme = "error"
        title_text = "Error"

        if error_type == ResponseType.AUTH_ERROR:
            theme = "auth_error"
            title_text = "Authentication Error"

        content = [TextElement(text=message, bold=False)]

        return cls(
            type=error_type,
            title=title_text,
            content=content,
            metadata={"theme": theme},
            error_code=error_code,
        )


class InfoResponse(StructuredMessage):
    """Response for informational messages."""

    type: ResponseType = Field(default=ResponseType.INFO)

    @classmethod
    def create(cls, message: str) -> "InfoResponse":
        """Create an InfoResponse with properly formatted content."""
        return cls(
            title="Information",
            content=[TextElement(text=message, bold=False)],
            metadata={"theme": "info"},
        )


class ResponseBuilder:
    """Helper class to build structured responses."""

    @staticmethod
    def success_meeting(
        event_id: str,
        title: str,
        start_time: str,
        end_time: str,
        *,
        event_link: Optional[str] = None,
        participants: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> MeetingSuccessResponse:
        """Build a successful meeting response."""
        calendar_link = None
        if event_link:
            calendar_link = LinkData(
                url=event_link, text="View in Calendar", external=True
            )

        meeting_data = MeetingEventData(
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location,
            participants=participants or [],
            calendar_link=calendar_link,
        )

        return MeetingSuccessResponse.create(meeting_data=meeting_data)

    @staticmethod
    def error(
        message: str,
        error_type: ResponseType = ResponseType.ERROR,
        error_code: Optional[str] = None,
    ) -> ErrorResponse:
        """Build an error response."""
        return ErrorResponse.create(
            message=message, error_type=error_type, error_code=error_code
        )

    @staticmethod
    def auth_error(message: str, error_code: Optional[str] = None) -> ErrorResponse:
        """Build an authentication error response."""
        return ErrorResponse.create(
            message=message, error_type=ResponseType.AUTH_ERROR, error_code=error_code
        )

    @staticmethod
    def info(message: str) -> InfoResponse:
        """Build an info response."""
        return InfoResponse.create(message=message)

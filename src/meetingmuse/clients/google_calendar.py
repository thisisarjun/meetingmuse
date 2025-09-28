from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from common.logger import Logger
from meetingmuse.models.meeting import (
    AttendeeDict,
    CalendarEventDetails,
    CalendarEventDict,
)
from server.services.oauth_service import OAuthService


class GoogleCalendarClient:
    """Client for interacting with Google Calendar API."""

    def __init__(self, oauth_service: OAuthService, logger: Logger) -> None:
        """Initialize the Google Calendar client.

        Args:
            oauth_service: OAuth service for authentication
            logger: Logger for logging operations
        """
        self.oauth_service = oauth_service
        self.logger = logger

    def _parse_datetime(self, date_time_str: Optional[str]) -> datetime:
        """Parse date time string to datetime object."""
        if not date_time_str:
            self.logger.warning("No date time provided, setting default")
            return datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=1)

        try:
            return datetime.strptime(date_time_str, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc
            )
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error parsing date time {date_time_str}: {str(e)}")
            return datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=1)

    def _parse_duration(self, duration_minutes: Optional[int]) -> int:
        """Get duration in minutes from integer value."""
        if duration_minutes is None:
            return 60  # Default to 1 hour

        # Validate the duration is reasonable (between 5 minutes and 8 hours)
        if not isinstance(duration_minutes, int) or duration_minutes < 5:
            self.logger.warning(f"Invalid duration {duration_minutes}, using default")
            return 60

        if duration_minutes > 480:  # 8 hours
            self.logger.warning(
                f"Duration {duration_minutes} minutes too long, capping at 480 minutes"
            )
            return 480

        return duration_minutes

    def _build_event_payload(
        self,
        title: Optional[str],
        start_time: datetime,
        end_time: datetime,
        *,
        location: Optional[str],
        attendees: list[AttendeeDict],
    ) -> CalendarEventDict:
        """Build the event payload for Google Calendar API.
        Args:
            title: Meeting title
            start_time: Meeting start time
            end_time: Meeting end time
            location: Meeting location
            attendees: List of attendees

        Returns:
            Dictionary containing the event payload
        """
        return {
            "summary": title or "Meeting",
            "location": location or "",
            "description": "Meeting created via MeetingMuse",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
            "attendees": attendees,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},  # 24 hours before
                    {"method": "popup", "minutes": 10},  # 10 minutes before
                ],
            },
        }

    def _prepare_attendees(
        self, participants: Optional[list[str]]
    ) -> list[AttendeeDict]:
        """Prepare attendees for the event payload."""
        attendees: list[AttendeeDict] = []
        if participants:
            for participant in participants:
                attendees.append({"email": participant})
        return attendees

    async def create_calendar_event(  # pylint: disable=too-many-positional-arguments
        self,
        session_id: str,
        title: Optional[str],
        date_time: Optional[str],
        duration_minutes: Optional[int],
        location: Optional[str] = None,
        participants: Optional[list[str]] = None,  # pylint: disable=unused-argument
    ) -> CalendarEventDetails:
        """Create a Google Calendar event.

        Args:
            session_id: OAuth session ID for authentication
            title: Meeting title
            date_time: Meeting date and time in YYYY-MM-DD HH:MM format
            duration_minutes: Meeting duration in minutes
            location: Meeting location (optional)
            participants: List of participant emails (optional)

        Returns:
            CalendarEventDetails with event information

        Raises:
            ValueError: If authentication fails or event creation fails
        """
        if not session_id:
            raise ValueError("No session ID available for calendar access")

        # Get OAuth credentials
        credentials = await self.oauth_service.get_credentials(session_id)
        if not credentials:
            raise ValueError("Could not obtain valid OAuth credentials")

        # Build Google Calendar service
        service = build("calendar", "v3", credentials=credentials)

        # Parse meeting details
        start_time = self._parse_datetime(date_time)
        parsed_duration = self._parse_duration(duration_minutes)
        end_time = start_time + timedelta(minutes=parsed_duration)

        # Prepare attendees
        attendees: list[AttendeeDict] = self._prepare_attendees(participants)

        # Create event object
        event = self._build_event_payload(
            title, start_time, end_time, location=location, attendees=attendees
        )

        try:
            # Insert the event
            created_event = (
                service.events()  # pylint: disable=no-member
                .insert(calendarId="primary", body=event)
                .execute()
            )
            return CalendarEventDetails(
                event_id=created_event["id"],
                event_link=created_event["htmlLink"],
                start_time=start_time.strftime("%Y-%m-%d %H:%M"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M"),
            )
        except HttpError as e:
            self.logger.error(f"Google Calendar API error: {str(e)}")
            raise ValueError(f"Failed to create calendar event: {str(e)}") from e

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.messages import AIMessage
from langgraph.types import Command

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.meeting import CalendarEventDetails
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import BaseNode
from server.services.oauth_service import OAuthService


class ScheduleMeetingNode(BaseNode):
    """
    Node that handles API calls for scheduling meetings.
    If the user intent is 'schedule', this node will attempt to schedule the meeting.
    On success, goes to END. On failure, goes to human interrupt retry node.
    """

    model: HuggingFaceModel
    oauth_service: OAuthService

    def __init__(
        self, model: HuggingFaceModel, logger: Logger, oauth_service: OAuthService
    ) -> None:
        """Initialize the node with model, logger, and OAuth service."""
        super().__init__(logger)
        self.model = model
        self.oauth_service = oauth_service

    # TODO: Modify prompt to return parsed datetime
    def _parse_datetime(self, date_time_str: Optional[str]) -> Optional[datetime]:
        """Parse date time string to datetime object."""
        if not date_time_str:
            return None

        try:
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%m/%d/%Y %H:%M",
                "%d/%m/%Y %H:%M",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_time_str, fmt)
                except ValueError:
                    continue

            self.logger.warning(f"Could not parse date time: {date_time_str}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing date time {date_time_str}: {str(e)}")
            return None

    # TODO: modify prompt to return parsed duration in minutes
    def _parse_duration(self, duration_str: Optional[str]) -> int:
        """Parse duration string to minutes."""
        if not duration_str:
            return 60  # Default to 1 hour

        try:
            duration_lower = duration_str.lower().strip()

            # Parse common formats
            if "hour" in duration_lower:
                hours = int("".join(filter(str.isdigit, duration_lower))) or 1
                return hours * 60
            elif "min" in duration_lower:
                return int("".join(filter(str.isdigit, duration_lower))) or 60
            else:
                # Try to extract number and assume minutes
                minutes = int("".join(filter(str.isdigit, duration_lower))) or 60
                return minutes
        except Exception as e:
            self.logger.error(f"Error parsing duration {duration_str}: {str(e)}")
            return 60  # Default to 1 hour

    async def _create_calendar_event(
        self, state: MeetingMuseBotState
    ) -> CalendarEventDetails:
        """Create a Google Calendar event."""
        if not state.session_id:
            raise ValueError("No session ID available for calendar access")

        # Get OAuth credentials
        credentials = await self.oauth_service.get_credentials(state.session_id)
        if not credentials:
            raise ValueError("Could not obtain valid OAuth credentials")

        # Build Google Calendar service
        service = build("calendar", "v3", credentials=credentials)

        # Parse meeting details
        start_time = self._parse_datetime(state.meeting_details.date_time)
        duration_minutes = self._parse_duration(state.meeting_details.duration)
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Prepare attendees
        attendees = []
        if state.meeting_details.participants:
            for participant in state.meeting_details.participants:
                attendees.append({"email": participant})

        # Create event object
        event = {
            "summary": state.meeting_details.title or "Meeting",
            "location": state.meeting_details.location or "",
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

        try:
            # Insert the event
            created_event = (
                service.events().insert(calendarId="primary", body=event).execute()
            )
            return CalendarEventDetails(
                event_id=created_event["id"],
                event_link=created_event.get("htmlLink"),
                start_time=start_time.strftime("%Y-%m-%d %H:%M"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M"),
            )
        except HttpError as e:
            self.logger.error(f"Google Calendar API error: {str(e)}")
            raise ValueError(f"Failed to create calendar event: {str(e)}")

    @log_node_entry(NodeName.SCHEDULE_MEETING)
    def node_action(self, state: MeetingMuseBotState) -> Command[Any]:
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            self.logger.error(
                f"No scheduling action needed for this intent: {state.user_intent}, wrong workflow"
            )
            message = "No scheduling action needed for this intent."
            state.messages.append(AIMessage(content=message))
            return Command(goto=NodeName.END)

        # Create calendar event using Google Calendar API
        try:
            # Check if session_id is available for authentication
            if not state.session_id:
                error_msg = (
                    "Authentication required to schedule meetings. Please log in first."
                )
                self.logger.error("No session ID available for calendar access")
                state.messages.append(AIMessage(content=f"ERROR {error_msg}"))
                return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)

            # Create calendar event
            self.logger.info("Creating Google Calendar event...")
            event_details = asyncio.run(self._create_calendar_event(state))

            # Success message
            success_message = (
                f"✅ Meeting scheduled successfully! \n"
                f"Event ID: {event_details.event_id} \n"
                f"Title: {state.meeting_details.title or 'Meeting'} \n"
                f"Time: {event_details.start_time} - {event_details.end_time} \n"
            )

            if event_details.event_link:
                success_message += f"Calendar Link: {event_details.event_link} \n"

            if state.meeting_details.participants:
                success_message += (
                    f"Participants: {', '.join(state.meeting_details.participants)} \n"
                )

            self.logger.info(
                f"Meeting scheduled successfully with ID: {event_details.event_id}"
            )
            state.messages.append(AIMessage(content=success_message))
            return Command(goto=NodeName.END)

        except ValueError as ve:
            # Handle authentication and validation errors
            auth_error_msg = f"Authentication error: {str(ve)}"
            self.logger.error(f"Authentication error in scheduling: {auth_error_msg}")
            state.messages.append(
                AIMessage(content=f"❌ {auth_error_msg}. Please re-authenticate.")
            )
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Handle all other errors
            exception_error_msg = f"Failed to schedule meeting: {str(e)}"
            self.logger.error(f"Exception in scheduling: {exception_error_msg}")
            state.messages.append(AIMessage(content=f"❌ {exception_error_msg}"))
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)

    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

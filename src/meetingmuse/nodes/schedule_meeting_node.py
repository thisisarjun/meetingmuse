import asyncio
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.types import Command

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.clients.google_calendar import GoogleCalendarClient
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import BaseNode


class ScheduleMeetingNode(BaseNode):
    """
    Node that handles API calls for scheduling meetings.
    If the user intent is 'schedule', this node will attempt to schedule the meeting.
    On success, goes to END. On failure, goes to human interrupt retry node.
    """

    model: HuggingFaceModel
    google_calendar_client: GoogleCalendarClient

    def __init__(
        self,
        model: HuggingFaceModel,
        logger: Logger,
        google_calendar_client: GoogleCalendarClient,
    ) -> None:
        """Initialize the node with model, logger, and Google Calendar client."""
        super().__init__(logger)
        self.model = model
        self.google_calendar_client = google_calendar_client

    @log_node_entry(NodeName.SCHEDULE_MEETING)
    def node_action(self, state: MeetingMuseBotState) -> Command[Any]:
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            self.logger.error(
                f"No scheduling action needed for this intent: {state.user_intent}, wrong workflow"
            )
            message = "No scheduling action needed for this intent."
            state.messages.append(AIMessage(content=message))
            return Command(goto=NodeName.END, update={"messages": state.messages})

        # Create calendar event using Google Calendar API
        try:
            # Check if session_id is available for authentication
            if not state.session_id:
                error_msg = (
                    "Authentication required to schedule meetings. Please log in first."
                )
                self.logger.error("No session ID available for calendar access")
                state.messages.append(AIMessage(content=f"ERROR {error_msg}"))
                return Command(
                    goto=NodeName.HUMAN_INTERRUPT_RETRY,
                    update={"messages": state.messages},
                )

            # Create calendar event
            self.logger.info("Creating Google Calendar event...")
            event_details = asyncio.run(
                self.google_calendar_client.create_calendar_event(
                    session_id=state.session_id,
                    title=state.meeting_details.title,
                    date_time=state.meeting_details.date_time,
                    duration_minutes=state.meeting_details.duration,
                    location=state.meeting_details.location,
                    participants=state.meeting_details.participants,
                )
            )

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
            return Command(goto=NodeName.END, update={"messages": state.messages})

        except ValueError as ve:
            # Handle authentication and validation errors
            auth_error_msg = f"Authentication error: {str(ve)}"
            self.logger.error(f"Authentication error in scheduling: {auth_error_msg}")
            state.messages.append(
                AIMessage(content=f"❌ {auth_error_msg}. Please re-authenticate.")
            )
            return Command(
                goto=NodeName.HUMAN_INTERRUPT_RETRY, update={"messages": state.messages}
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Handle all other errors
            exception_error_msg = f"Failed to schedule meeting: {str(e)}"
            self.logger.error(f"Exception in scheduling: {exception_error_msg}")
            state.messages.append(AIMessage(content=f"❌ {exception_error_msg}"))
            return Command(
                goto=NodeName.HUMAN_INTERRUPT_RETRY, update={"messages": state.messages}
            )

    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

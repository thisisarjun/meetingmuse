import asyncio
import json
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.types import Command

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.clients.google_calendar import GoogleCalendarClient
from meetingmuse.llm_models.hugging_face import BaseLlmModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.response import ResponseBuilder, ResponseType, StructuredMessage
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import BaseNode


class ScheduleMeetingNode(BaseNode):
    """
    Node that handles API calls for scheduling meetings.
    If the user intent is 'schedule', this node will attempt to schedule the meeting.
    On success, goes to END. On failure, goes to human interrupt retry node.
    """

    model: BaseLlmModel
    google_calendar_client: GoogleCalendarClient

    def __init__(
        self,
        model: BaseLlmModel,
        logger: Logger,
        google_calendar_client: GoogleCalendarClient,
    ) -> None:
        """Initialize the node with model, logger, and Google Calendar client."""
        super().__init__(logger)
        self.model = model
        self.google_calendar_client = google_calendar_client
        self.response_builder = ResponseBuilder()

    def _create_structured_message(self, response_obj: StructuredMessage) -> AIMessage:
        """Create an AIMessage with structured response data."""
        # Convert the structured response to JSON for frontend parsing
        structured_data = {
            "structured_response": True,
            "data": response_obj.model_dump(),
        }
        return AIMessage(content=json.dumps(structured_data, ensure_ascii=False))

    @log_node_entry(NodeName.SCHEDULE_MEETING)
    def node_action(self, state: MeetingMuseBotState) -> Command[Any]:
        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            self.logger.error(
                f"No scheduling action needed for this intent: {state.user_intent}, wrong workflow"
            )
            message = self._create_structured_message(
                self.response_builder.info(
                    "No scheduling action needed for this intent."
                )
            )
            state.messages.append(message)
            return Command(goto=NodeName.END, update={"messages": state.messages})

        # Create calendar event using Google Calendar API
        try:
            # Check if session_id is available for authentication
            if not state.session_id:
                error_msg = (
                    "Authentication required to schedule meetings. Please log in first."
                )
                self.logger.error("No session ID available for calendar access")
                message = self._create_structured_message(
                    self.response_builder.auth_error(
                        error_msg, error_code="NO_SESSION_ID"
                    )
                )
                state.messages.append(message)
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

            # if event_details.event_link:
            #     success_message += f"Calendar Link: {event_details.event_link} \n"
            #
            # if state.meeting_details.participants:
            #     success_message += (
            #         f"Participants: {', '.join(state.meeting_details.participants)} \n"
            #     )

            self.logger.info(
                f"Meeting scheduled successfully with ID: {event_details.event_id}"
            )
            message = self._create_structured_message(
                self.response_builder.success_meeting(
                    event_id=event_details.event_id,
                    title=state.meeting_details.title or "Meeting",
                    start_time=event_details.start_time,
                    end_time=event_details.end_time,
                    event_link=event_details.event_link,
                    participants=state.meeting_details.participants,
                    location=state.meeting_details.location,
                )
            )
            state.messages.append(message)
            return Command(goto=NodeName.END, update={"messages": state.messages})

        except ValueError as ve:
            # Handle authentication and validation errors
            auth_error_msg = f"Authentication error: {str(ve)}. Please re-authenticate."
            self.logger.error(f"Authentication error in scheduling: {auth_error_msg}")
            message = self._create_structured_message(
                self.response_builder.auth_error(
                    auth_error_msg, error_code="AUTH_VALIDATION_ERROR"
                )
            )
            state.messages.append(message)
            return Command(
                goto=NodeName.HUMAN_INTERRUPT_RETRY, update={"messages": state.messages}
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Handle all other errors
            exception_error_msg = f"Failed to schedule meeting: {str(e)}"
            self.logger.error(f"Exception in scheduling: {exception_error_msg}")
            message = self._create_structured_message(
                self.response_builder.error(
                    exception_error_msg,
                    error_type=ResponseType.ERROR,
                    error_code="CALENDAR_API_ERROR",
                )
            )
            state.messages.append(message)
            return Command(
                goto=NodeName.HUMAN_INTERRUPT_RETRY, update={"messages": state.messages}
            )

    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

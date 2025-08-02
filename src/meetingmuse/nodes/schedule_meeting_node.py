import random
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.types import Command

from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.utils.logger import Logger


class ScheduleMeetingNode(BaseNode):
    """
    Node that handles API calls for scheduling meetings.
    If the user intent is 'schedule', this node will attempt to schedule the meeting.
    On success, goes to END. On failure, goes to human interrupt retry node.
    """

    model: HuggingFaceModel
    logger: Logger

    def __init__(self, model: HuggingFaceModel, logger: Logger) -> None:
        """Initialize the node with model and logger."""
        self.model = model
        self.logger = logger

    def node_action(self, state: MeetingMuseBotState) -> Command[Any]:
        self.logger.info("Starting meeting scheduling process")

        # Check if user intent is schedule
        if state.user_intent != UserIntent.SCHEDULE_MEETING:
            self.logger.error(
                f"No scheduling action needed for this intent: {state.user_intent}, wrong workflow"
            )
            message = "No scheduling action needed for this intent."
            state.messages.append(AIMessage(content=message))
            return Command(goto=NodeName.END)

        # Simulate API call to schedule meeting
        # TODO: Replace with actual API call logic
        try:
            # Simulate API call (30% success rate for demo purposes)
            success_probability: float = random.random()
            if success_probability < 0.3:
                # Success case
                meeting_id = f"MTG_{random.randint(1000, 9999)}"
                success_message = (
                    f"✅ Meeting scheduled successfully! "
                    f"Meeting ID: {meeting_id}. "
                    f"Title: {state.meeting_details.title or 'Meeting'}, "
                    f"Time: {state.meeting_details.date_time or 'TBD'}"
                )
                self.logger.info(
                    f"Meeting scheduled successfully with ID: {meeting_id}"
                )
                state.messages.append(AIMessage(content=success_message))
                return Command(goto=NodeName.END)
            # Failure case
            raise Exception("Meeting scheduling failed")

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Exception handling
            exception_error_msg = f"Unexpected error during scheduling: {str(e)}"
            self.logger.error(f"Exception in scheduling: {exception_error_msg}")
            state.messages.append(AIMessage(content=f"❌ {exception_error_msg}"))
            return Command(goto=NodeName.HUMAN_INTERRUPT_RETRY)

    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING

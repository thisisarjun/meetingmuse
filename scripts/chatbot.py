from typing import Any, Optional

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from common.logger import Logger
from common.utils import Utils
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState


class ChatBot:
    def __init__(self, graph: Any) -> None:
        self.graph = graph
        self.thread_id = "conversation_1"
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.initial_state = MeetingMuseBotState(
            messages=[], user_intent=None, meeting_details=MeetingFindings()
        )
        self.logger = Logger()

    def get_last_message(self, events: dict[str, Any]) -> Optional[str]:
        # Skip interrupt events
        if "__interrupt__" in events:
            return None

        # Get the state from the node result
        return Utils.get_last_message_from_events(events, "ai")
        # for state in events.values():
        #     self.logger.info(f"State: {type(state)}")
        #     if hasattr(state, "messages") and state.messages:
        #         message = state.messages[-1]
        #         if message and message.type == "ai" and message.content:
        #             return str(message.content)
        # return None

    def process_input(self, user_input: str) -> None:
        # Always add the user message and process
        self.initial_state.messages.append(HumanMessage(content=user_input))

        for events in self.graph.stream(self.initial_state, config=self.config):
            if "__interrupt__" in events:
                interrupt_info = events["__interrupt__"][0]
                user_input = input(f"{interrupt_info.value.question} \n User: ")
                for _resume_chunk in self.graph.stream(
                    Command(resume=user_input), self.config, stream_mode="values"
                ):
                    pass
                return

            message = self.get_last_message(events)
            if message:
                print("Assistant:", message)

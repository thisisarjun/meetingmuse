from typing import Any, Optional

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from meetingmuse.graph import GraphBuilder
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.utils.logger import Logger
from scripts.common import initialize_nodes

logger = Logger()
nodes = initialize_nodes()
model = nodes["model"]
intent_classifier = nodes["intent_classifier"]
classify_intent_node = nodes["classify_intent_node"]
greeting_node = nodes["greeting_node"]
collecting_info_node = nodes["collecting_info_node"]
clarify_request_node = nodes["clarify_request_node"]
meeting_details_service = nodes["meeting_details_service"]
human_schedule_meeting_more_info_node = nodes["human_schedule_meeting_more_info_node"]
prompt_missing_meeting_details_node = nodes["prompt_missing_meeting_details_node"]
schedule_meeting_node = nodes["schedule_meeting_node"]
human_interrupt_retry_node = nodes["human_interrupt_retry_node"]
conversation_router = nodes["conversation_router"]
end_node = nodes["end_node"]


class ChatBot:
    def __init__(self, graph: Any) -> None:
        self.graph = graph
        self.thread_id = "conversation_1"
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.initial_state = MeetingMuseBotState(
            messages=[], user_intent=None, meeting_details=MeetingFindings()
        )

    def get_last_message(self, events: dict[str, Any]) -> Optional[str]:
        # Skip interrupt events
        if "__interrupt__" in events:
            return None

        # Get the state from the node result
        for state in events.values():
            if hasattr(state, "messages") and state.messages:
                message = state.messages[-1]
                if message and message.type == "ai" and message.content:
                    return str(message.content)
        return None

    def process_input(self, user_input: str) -> None:
        # Always add the user message and process
        self.initial_state.messages.append(HumanMessage(content=user_input))

        for events in self.graph.stream(self.initial_state, config=self.config):
            if "__interrupt__" in events:
                interrupt_info = events["__interrupt__"][0]
                user_input = input(f"{interrupt_info.value.question} ")
                for _resume_chunk in self.graph.stream(
                    Command(resume=user_input), self.config, stream_mode="values"
                ):
                    pass
                return

            message = self.get_last_message(events)
            if message:
                print("Assistant:", message)


if __name__ == "__main__":
    graph_builder = GraphBuilder(
        state=MeetingMuseBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        collecting_info_node=collecting_info_node,
        schedule_meeting_node=schedule_meeting_node,
        human_interrupt_retry_node=human_interrupt_retry_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
        human_schedule_meeting_more_info_node=human_schedule_meeting_more_info_node,
        prompt_missing_meeting_details_node=prompt_missing_meeting_details_node,
        end_node=end_node,
    )
    graph = graph_builder.build()
    chatbot = ChatBot(graph)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            chatbot.process_input(user_input)
        except Exception as e:
            print(e)
            break

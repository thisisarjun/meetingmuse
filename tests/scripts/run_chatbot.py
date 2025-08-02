from langchain_core.messages import HumanMessage
from langgraph.types import Command

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.end_node import EndNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode
from meetingmuse.nodes.human_schedule_meeting_more_info_node import (
    HumanScheduleMeetingMoreInfoNode,
)
from meetingmuse.nodes.prompt_missing_meeting_details_node import (
    PromptMissingMeetingDetailsNode,
)
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger

logger = Logger()
conversation_router = ConversationRouter(logger)
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier)
greeting_node = GreetingNode(model)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model)
meeting_details_service = MeetingDetailsService(model, logger)
human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger)
prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
    logger, meeting_details_service
)
schedule_meeting_node = ScheduleMeetingNode(model, logger)
human_interrupt_retry_node = HumanInterruptRetryNode(logger)
end_node = EndNode()


class ChatBot:
    def __init__(self, graph):
        self.graph = graph
        self.thread_id = "conversation_1"
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.initial_state = MeetingMuseBotState(
            messages=[], user_intent=None, meeting_details=MeetingFindings()
        )

    def get_last_message(self, events: dict):
        # Skip interrupt events
        if "__interrupt__" in events:
            return None

        # Get the state from the node result
        for state in events.values():
            if hasattr(state, "messages") and state.messages:
                message = state.messages[-1]
                if message and message.type == "ai" and message.content:
                    return message.content
        return None

    def process_input(self, user_input: str):
        # Always add the user message and process
        self.initial_state.messages.append(HumanMessage(content=user_input))

        for events in self.graph.stream(self.initial_state, config=self.config):
            if "__interrupt__" in events:
                interrupt_info = events["__interrupt__"][0]
                user_input = input(f"{interrupt_info.value} ")
                for _resume_chunk in self.graph.stream(
                    Command(resume=user_input), self.config, stream_mode="values"
                ):
                    print(f"🆔 resume_chunk: {_resume_chunk}")
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

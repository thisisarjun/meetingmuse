from typing import Any

from common.logger import Logger
from meetingmuse.graph.graph import GraphBuilder
from meetingmuse.llm_models.factory import create_llm_model
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

logger = Logger()
model = create_llm_model("gpt-4o-mini", "openai")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier, logger)
greeting_node = GreetingNode(model, logger)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model, logger)
conversation_router = ConversationRouter(logger)
meeting_details_service = MeetingDetailsService(model, logger)
human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger)
prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
    meeting_details_service, logger
)
schedule_meeting_node = ScheduleMeetingNode(model, logger)
human_interrupt_retry_node = HumanInterruptRetryNode(logger)
end_node = EndNode(logger)


def draw_graph(graph_builder: Any) -> None:
    try:
        graph: Any = graph_builder.build()
        with open("graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved as graph.png")
    except Exception as e:
        print(f"Could not generate graph: {e}")
        raise e


def create_graph_with_all_nodes() -> GraphBuilder:
    graph_builder = GraphBuilder(
        state=MeetingMuseBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        collecting_info_node=collecting_info_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
        human_schedule_meeting_more_info_node=human_schedule_meeting_more_info_node,
        prompt_missing_meeting_details_node=prompt_missing_meeting_details_node,
        schedule_meeting_node=schedule_meeting_node,
        human_interrupt_retry_node=human_interrupt_retry_node,
        end_node=end_node,
    )
    return graph_builder


def generate_graph() -> None:
    graph_builder = create_graph_with_all_nodes()
    draw_graph(graph_builder)


if __name__ == "__main__":
    generate_graph()

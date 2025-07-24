
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import CalendarBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.process_request_node import ProcessRequestNode
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger

logger = Logger()
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier)
greeting_node = GreetingNode(model)
schedule_meeting_node = ScheduleMeetingNode(model)
clarify_request_node = ClarifyRequestNode(model)
process_request_node = ProcessRequestNode()
conversation_router = ConversationRouter(logger)

def create_intent_test_graph():
    workflow = StateGraph(CalendarBotState)
    
    # Add only the intent classification node
    workflow.add_node("classify_intent", classify_intent_node.node_action)
    
    # Simple flow: START -> classify_intent -> END
    workflow.add_edge(START, "classify_intent")
    workflow.add_edge("classify_intent", END)
    return workflow.compile()


def create_greeting_test_graph():
    workflow = StateGraph(CalendarBotState)
    workflow.add_node("greeting", greeting_node.node_action)
    workflow.add_edge(START, "greeting")
    workflow.add_edge("greeting", END)
    return workflow.compile()


def create_schedule_meeting_test_graph():
    workflow = StateGraph(CalendarBotState)
    workflow.add_node("schedule_meeting", schedule_meeting_node.node_action)
    workflow.add_edge(START, "schedule_meeting")
    workflow.add_edge("schedule_meeting", END)
    return workflow.compile()

def create_clarify_request_test_graph():
    workflow = StateGraph(CalendarBotState)
    workflow.add_node("clarify_request", clarify_request_node.node_action)
    workflow.add_edge(START, "clarify_request")
    workflow.add_edge("clarify_request", END)
    return workflow.compile()

def create_process_request_test_graph():
    workflow = StateGraph(CalendarBotState)
    workflow.add_node("process_request", process_request_node.node_action)
    workflow.add_edge(START, "process_request")
    workflow.add_edge("process_request", END)
    return workflow.compile()

def create_graph_with_all_nodes():
    graph_builder = GraphBuilder(
        state=CalendarBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        schedule_meeting_node=schedule_meeting_node,
        process_request_node=process_request_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
    )
    return graph_builder

if __name__ == "__main__":

    
    # graph = create_intent_test_graph()
    # graph = create_greeting_test_graph()
    # graph = create_schedule_meeting_test_graph()
    # graph = create_clarify_request_test_graph()
    # output = graph.invoke({"messages": [HumanMessage("bla bla bla")]})
    # logger.info(f"Graph output: {output}")
    graph_builder = create_graph_with_all_nodes()
    graph_builder.draw_graph()
    

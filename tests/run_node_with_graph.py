
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.state import ConversationStep

logger = Logger()
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier)
greeting_node = GreetingNode(model)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model)
conversation_router = ConversationRouter(logger)

def create_initial_state_for_testing(user_message: str) -> MeetingMuseBotState:
    return MeetingMuseBotState(
        messages=[HumanMessage(content=user_message)],
        user_intent=None,
        current_step=ConversationStep.GREETING,
        meeting_details=MeetingFindings()
    )

def create_intent_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    
    # Add only the intent classification node
    workflow.add_node("classify_intent", classify_intent_node.node_action)
    
    # Simple flow: START -> classify_intent -> END
    workflow.add_edge(START, "classify_intent")
    workflow.add_edge("classify_intent", END)
    return workflow.compile()


def create_greeting_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("greeting", greeting_node.node_action)
    workflow.add_edge(START, "greeting")
    workflow.add_edge("greeting", END)
    return workflow.compile()


def create_collecting_info_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("collecting_info", collecting_info_node.node_action)
    workflow.add_edge(START, "collecting_info")
    workflow.add_edge("collecting_info", END)
    return workflow.compile()

def create_clarify_request_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("clarify_request", clarify_request_node.node_action)
    workflow.add_edge(START, "clarify_request")
    workflow.add_edge("clarify_request", END)
    return workflow.compile()



def create_graph_with_all_nodes() -> GraphBuilder:
    graph_builder = GraphBuilder(
        state=MeetingMuseBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        collecting_info_node=collecting_info_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
    )
    return graph_builder

def test_single_node(node_name: NodeName, user_message: str):
    
    initial_state = create_initial_state_for_testing(user_message)
    
    if node_name == NodeName.CLASSIFY_INTENT:
        graph = create_intent_test_graph()
    elif node_name == NodeName.GREETING:
        graph = create_greeting_test_graph()
    elif node_name == NodeName.COLLECTING_INFO:
        graph = create_collecting_info_test_graph()
    elif node_name == NodeName.CLARIFY_REQUEST:
        graph = create_clarify_request_test_graph()    
    
    result = graph.invoke(initial_state)
    logger.info(f"Final state: {result}")
    return result

def draw_graph():
    graph_builder = create_graph_with_all_nodes()
    graph_builder.draw_graph()

if __name__ == "__main__":
    # this method draws the graph - if you want to visualize the graph,
    draw_graph()
    # use this method, change NodeName value to test different node.
    # NOTE: make sure that the new node is added and helper method is     
    test_single_node(NodeName.COLLECTING_INFO, "I want to schedule a meeting with John Doe on 2025-08-01 at 10:00 AM for 1 hour")


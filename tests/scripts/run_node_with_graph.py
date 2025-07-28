import argparse
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.human_schedule_meeting_more_info_node import HumanScheduleMeetingMoreInfoNode
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger
from meetingmuse.models.meeting import MeetingFindings

logger = Logger()
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier)
greeting_node = GreetingNode(model)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model)
conversation_router = ConversationRouter(logger)
meeting_details_service = MeetingDetailsService(model, logger)
human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger, meeting_details_service)

def create_initial_state_for_testing(user_message: str) -> MeetingMuseBotState:
    return MeetingMuseBotState(
        messages=[HumanMessage(content=user_message)],
        user_intent=None,
        meeting_details=MeetingFindings()
    )

def create_intent_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    
    # Add only the intent classification node
    workflow.add_node("classify_intent", classify_intent_node.node_action)
    
    # Simple flow: START -> classify_intent -> END
    workflow.add_edge(START, "classify_intent")
    workflow.add_edge("classify_intent", END)
    return workflow


def create_greeting_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("greeting", greeting_node.node_action)
    workflow.add_edge(START, "greeting")
    workflow.add_edge("greeting", END)
    return workflow

def create_collecting_info_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("collecting_info", collecting_info_node.node_action)
    workflow.add_edge(START, "collecting_info")
    workflow.add_edge("collecting_info", END)
    return workflow

def create_clarify_request_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("clarify_request", clarify_request_node.node_action)
    workflow.add_edge(START, "clarify_request")
    workflow.add_edge("clarify_request", END)
    return workflow

def create_human_schedule_meeting_more_info_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node("human_schedule_meeting_more_info", human_schedule_meeting_more_info_node.node_action)
    workflow.add_node("collecting_info", collecting_info_node.node_action)
    
    workflow.add_edge(START, "human_schedule_meeting_more_info")
    workflow.add_edge("collecting_info", END)
    return workflow

def test_single_node(node_name: NodeName, user_message: str):
    
    initial_state = create_initial_state_for_testing(user_message)
    
    if node_name == NodeName.CLASSIFY_INTENT:
        workflow = create_intent_test_graph()
    elif node_name == NodeName.GREETING:
        workflow = create_greeting_test_graph()
    elif node_name == NodeName.COLLECTING_INFO:
        workflow = create_collecting_info_test_graph()
    elif node_name == NodeName.CLARIFY_REQUEST:
        workflow = create_clarify_request_test_graph()    
    elif node_name == NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO:
        workflow = create_human_schedule_meeting_more_info_test_graph()
    
    graph = workflow.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test"}}
    result = graph.invoke(initial_state, config=config)
    logger.info(f"Final state: {result}")
    return result

def interrupt_node(node_name: NodeName, user_message: str):
    initial_state = create_initial_state_for_testing(user_message)
    if node_name == NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO:
        workflow = create_human_schedule_meeting_more_info_test_graph()
    else:
        raise ValueError(f"Node {node_name} does not support interruption")
    
    graph = workflow.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test"}}
    
    for chunk in graph.stream(initial_state, config):
        print(f"🤔 chunk: {chunk}")
        if "__interrupt__" in chunk:
            interrupt_info = chunk["__interrupt__"][0]
            user_input = input(f"{interrupt_info.value} ")
            for resume_chunk in graph.stream(Command(resume=user_input), config):
                logger.info(f"🆔 resume_chunk: {resume_chunk}")


def parse_args():
    parser = argparse.ArgumentParser(description="Debug individual nodes in isolation")
    parser.add_argument("--node", type=str, required=True, 
                       choices=["CLASSIFY_INTENT", "GREETING", "COLLECTING_INFO", "CLARIFY_REQUEST", "HUMAN_SCHEDULE_MEETING_MORE_INFO"],
                       help="Node name to test")
    parser.add_argument("--message", type=str, required=True, help="User message to test with")
    parser.add_argument("--interrupt", action="store_true", help="Test node with interruption support (streaming)")
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
        
    args = parse_args()    
    
    node_name = getattr(NodeName, args.node)
    
    if args.interrupt:
        interrupt_node(node_name, args.message)
    else:
        test_single_node(node_name, args.message)


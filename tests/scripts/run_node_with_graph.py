import argparse
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.human_schedule_meeting_more_info_node import HumanScheduleMeetingMoreInfoNode
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode
from meetingmuse.nodes.human_interrupt_retry_node import HumanInterruptRetryNode
from meetingmuse.nodes.prompt_missing_meeting_details_node import PromptMissingMeetingDetailsNode
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
schedule_meeting_node = ScheduleMeetingNode(model, logger)
human_interrupt_retry_node = HumanInterruptRetryNode(model, logger)
conversation_router = ConversationRouter(logger)
meeting_details_service = MeetingDetailsService(model, logger)
human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger)
prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(logger, meeting_details_service)

def create_initial_state_for_testing(user_message: str) -> MeetingMuseBotState:
    return MeetingMuseBotState(
        messages=[HumanMessage(content=user_message)],
        user_intent=UserIntent.SCHEDULE_MEETING,
        meeting_details=MeetingFindings(date_time='2023-10-01T10:00:00Z', duration='60 minutes', title='Test Meeting', participants=['me', 'you'])
    )

def create_intent_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    
    # Add only the intent classification node
    workflow.add_node(NodeName.CLASSIFY_INTENT, classify_intent_node.node_action)
    
    # Simple flow: START -> classify_intent -> END
    workflow.add_edge(START, NodeName.CLASSIFY_INTENT)
    workflow.add_edge(NodeName.CLASSIFY_INTENT, END)
    return workflow


def create_greeting_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.GREETING, greeting_node.node_action)
    workflow.add_edge(START, NodeName.GREETING)
    workflow.add_edge(NodeName.GREETING, END)
    return workflow

def create_collecting_info_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.COLLECTING_INFO, collecting_info_node.node_action)
    workflow.add_edge(START, NodeName.COLLECTING_INFO)
    workflow.add_edge(NodeName.COLLECTING_INFO, END)
    return workflow

def create_clarify_request_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.CLARIFY_REQUEST, clarify_request_node.node_action)
    workflow.add_edge(START, NodeName.CLARIFY_REQUEST)
    workflow.add_edge(NodeName.CLARIFY_REQUEST, END)
    return workflow

def create_schedule_meeting_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.SCHEDULE_MEETING, schedule_meeting_node.node_action)
    workflow.add_node(NodeName.HUMAN_INTERRUPT_RETRY, human_interrupt_retry_node.node_action)
    workflow.add_edge(START, NodeName.SCHEDULE_MEETING)
    workflow.add_edge(NodeName.HUMAN_INTERRUPT_RETRY, END)
    return workflow.compile()

def create_human_schedule_meeting_more_info_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO, human_schedule_meeting_more_info_node.node_action)
    workflow.add_node(NodeName.COLLECTING_INFO, collecting_info_node.node_action)
    
    workflow.add_edge(START, NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO)
    workflow.add_edge(NodeName.COLLECTING_INFO, END)
    return workflow

def create_prompt_missing_meeting_details_test_graph():
    workflow = StateGraph(MeetingMuseBotState)
    workflow.add_node(NodeName.PROMPT_MISSING_MEETING_DETAILS, prompt_missing_meeting_details_node.node_action)
    workflow.add_node(NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO, human_schedule_meeting_more_info_node.node_action)
    workflow.add_edge(START, NodeName.PROMPT_MISSING_MEETING_DETAILS)
    workflow.add_edge(NodeName.PROMPT_MISSING_MEETING_DETAILS, NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO)
    workflow.add_edge(NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO, END)
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
    elif node_name == NodeName.SCHEDULE_MEETING:
        workflow = create_schedule_meeting_test_graph()
    elif node_name == NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO:
        workflow = create_human_schedule_meeting_more_info_test_graph()
    elif node_name == NodeName.PROMPT_MISSING_MEETING_DETAILS:
        workflow = create_prompt_missing_meeting_details_test_graph()
    
    graph = workflow.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "test"}}
    result = graph.invoke(initial_state, config=config)
    logger.info(f"Final state: {result}")
    return result

def interrupt_node(node_name: NodeName, user_message: str):
    initial_state = create_initial_state_for_testing(user_message)
    if node_name not in [NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO, NodeName.PROMPT_MISSING_MEETING_DETAILS]:
        raise ValueError(f"Node {node_name} does not support interruption")    
    if node_name == NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO:
        workflow = create_human_schedule_meeting_more_info_test_graph()
    elif node_name == NodeName.PROMPT_MISSING_MEETING_DETAILS:
        workflow = create_prompt_missing_meeting_details_test_graph()
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
                       choices=[node.name for node in NodeName],
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


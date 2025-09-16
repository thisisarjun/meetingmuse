"""
MeetingMuse LangGraph Workflow
"""

from typing import Type

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from meetingmuse.models.node import NodeName
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
from meetingmuse.services.routing_service import ConversationRouter


class GraphBuilder:  # pylint: disable=too-many-instance-attributes
    state: Type[MeetingMuseBotState]
    greeting_node: GreetingNode
    clarify_request_node: ClarifyRequestNode
    collecting_info_node: CollectingInfoNode
    classify_intent_node: ClassifyIntentNode
    schedule_meeting_node: ScheduleMeetingNode
    human_interrupt_retry_node: HumanInterruptRetryNode
    conversation_router: ConversationRouter
    human_schedule_meeting_more_info_node: HumanScheduleMeetingMoreInfoNode
    prompt_missing_meeting_details_node: PromptMissingMeetingDetailsNode
    end_node: EndNode

    def __init__(  # pylint: disable=too-many-positional-arguments,too-many-arguments
        self,
        state: Type[MeetingMuseBotState],
        greeting_node: GreetingNode,
        clarify_request_node: ClarifyRequestNode,
        collecting_info_node: CollectingInfoNode,
        classify_intent_node: ClassifyIntentNode,
        schedule_meeting_node: ScheduleMeetingNode,
        human_interrupt_retry_node: HumanInterruptRetryNode,
        conversation_router: ConversationRouter,
        human_schedule_meeting_more_info_node: HumanScheduleMeetingMoreInfoNode,
        prompt_missing_meeting_details_node: PromptMissingMeetingDetailsNode,
        end_node: EndNode,
    ) -> None:
        self.state = state
        self.greeting_node = greeting_node
        self.clarify_request_node = clarify_request_node
        self.collecting_info_node = collecting_info_node
        self.classify_intent_node = classify_intent_node
        self.schedule_meeting_node = schedule_meeting_node
        self.human_interrupt_retry_node = human_interrupt_retry_node
        self.conversation_router = conversation_router
        self.human_schedule_meeting_more_info_node = (
            human_schedule_meeting_more_info_node
        )
        self.prompt_missing_meeting_details_node = prompt_missing_meeting_details_node
        self.end_node = end_node

    def build(self) -> CompiledStateGraph:
        graph_builder: StateGraph = StateGraph(self.state)
        graph_builder.add_node(
            self.greeting_node.node_name, self.greeting_node.node_action
        )
        graph_builder.add_node(
            self.classify_intent_node.node_name, self.classify_intent_node.node_action
        )
        graph_builder.add_node(
            self.clarify_request_node.node_name, self.clarify_request_node.node_action
        )
        graph_builder.add_node(
            self.collecting_info_node.node_name, self.collecting_info_node.node_action
        )
        graph_builder.add_node(
            self.prompt_missing_meeting_details_node.node_name,
            self.prompt_missing_meeting_details_node.node_action,
        )
        graph_builder.add_node(
            self.human_schedule_meeting_more_info_node.node_name,
            self.human_schedule_meeting_more_info_node.node_action,
        )
        graph_builder.add_node(
            self.schedule_meeting_node.node_name, self.schedule_meeting_node.node_action
        )
        graph_builder.add_node(
            self.human_interrupt_retry_node.node_name,
            self.human_interrupt_retry_node.node_action,
        )
        graph_builder.add_node(self.end_node.node_name, self.end_node.node_action)

        # Edges
        graph_builder.add_edge(START, self.classify_intent_node.node_name)
        # add conditional route using the routing service
        graph_builder.add_conditional_edges(
            self.classify_intent_node.node_name,
            self.conversation_router.intent_to_node_name_router,
            {
                NodeName.GREETING: NodeName.GREETING,
                NodeName.COLLECTING_INFO: NodeName.COLLECTING_INFO,
                NodeName.CLARIFY_REQUEST: NodeName.CLARIFY_REQUEST,
            },
        )
        graph_builder.add_conditional_edges(
            self.collecting_info_node.node_name,
            self.collecting_info_node.get_next_node_name,
            {
                NodeName.SCHEDULE_MEETING: NodeName.SCHEDULE_MEETING,
                NodeName.PROMPT_MISSING_MEETING_DETAILS: NodeName.PROMPT_MISSING_MEETING_DETAILS,
            },
        )
        graph_builder.add_conditional_edges(
            self.prompt_missing_meeting_details_node.node_name,
            self.prompt_missing_meeting_details_node.get_next_node,
            {
                NodeName.END: NodeName.END,
                NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO: self.human_schedule_meeting_more_info_node.node_name,
            },
        )
        graph_builder.add_edge(
            self.human_schedule_meeting_more_info_node.node_name,
            self.collecting_info_node.node_name,
        )
        # Add edges to END for completion
        graph_builder.add_edge(self.greeting_node.node_name, self.end_node.node_name)
        graph_builder.add_edge(
            self.clarify_request_node.node_name, self.end_node.node_name
        )
        graph_builder.add_edge(self.end_node.node_name, END)

        return graph_builder.compile(checkpointer=InMemorySaver())

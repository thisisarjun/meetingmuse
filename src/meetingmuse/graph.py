"""
MeetingMuse LangGraph Workflow
"""

from typing import Any, Type

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.human_schedule_meeting_more_info_node import (
    HumanScheduleMeetingMoreInfoNode,
)
from meetingmuse.nodes.prompt_missing_meeting_details_node import (
    PromptMissingMeetingDetailsNode,
)
from meetingmuse.services.routing_service import ConversationRouter


class GraphBuilder:
    state: Type[MeetingMuseBotState]
    greeting_node: GreetingNode
    clarify_request_node: ClarifyRequestNode
    collecting_info_node: CollectingInfoNode
    classify_intent_node: ClassifyIntentNode
    conversation_router: ConversationRouter
    human_schedule_meeting_more_info_node: HumanScheduleMeetingMoreInfoNode
    prompt_missing_meeting_details_node: PromptMissingMeetingDetailsNode

    def __init__(
        self,
        state: Type[MeetingMuseBotState],
        greeting_node: GreetingNode,
        clarify_request_node: ClarifyRequestNode,
        collecting_info_node: CollectingInfoNode,
        classify_intent_node: ClassifyIntentNode,
        conversation_router: ConversationRouter,
        human_schedule_meeting_more_info_node: HumanScheduleMeetingMoreInfoNode,
        prompt_missing_meeting_details_node: PromptMissingMeetingDetailsNode,
    ) -> None:
        self.state = state
        self.greeting_node = greeting_node
        self.clarify_request_node = clarify_request_node
        self.collecting_info_node = collecting_info_node
        self.classify_intent_node = classify_intent_node
        self.conversation_router = conversation_router
        self.human_schedule_meeting_more_info_node = (
            human_schedule_meeting_more_info_node
        )
        self.prompt_missing_meeting_details_node = prompt_missing_meeting_details_node

    def build(self) -> Any:
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
                # TODO: should go to schedule meeting node
                NodeName.END: END,
                NodeName.PROMPT_MISSING_MEETING_DETAILS: NodeName.PROMPT_MISSING_MEETING_DETAILS,
            },
        )
        graph_builder.add_conditional_edges(
            self.prompt_missing_meeting_details_node.node_name,
            self.prompt_missing_meeting_details_node.get_next_node,
            {
                NodeName.END: END,
                NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO: self.human_schedule_meeting_more_info_node.node_name,
            },
        )
        graph_builder.add_edge(
            self.human_schedule_meeting_more_info_node.node_name,
            self.collecting_info_node.node_name,
        )
        # Add edges to END for completion
        graph_builder.add_edge(self.greeting_node.node_name, END)
        graph_builder.add_edge(self.clarify_request_node.node_name, END)

        return graph_builder.compile(checkpointer=InMemorySaver())

    def draw_graph(self) -> None:
        try:
            graph: Any = self.build()
            with open("graph.png", "wb") as f:
                f.write(graph.get_graph().draw_mermaid_png())
            print("Graph saved as graph.png")
        except Exception as e:
            print(f"Could not generate graph: {e}")
            raise e

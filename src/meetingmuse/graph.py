"""
MeetingMuse LangGraph Workflow
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

from meetingmuse.models.state import CalendarBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.process_request_node import ProcessRequestNode
from meetingmuse.nodes.schedule_meeting_node import ScheduleMeetingNode


class GraphBuilder:
    def __init__(self, 
        state: CalendarBotState,
        greeting_node: GreetingNode,
        clarify_request_node: ClarifyRequestNode,
        schedule_meeting_node: ScheduleMeetingNode,
        process_request_node: ProcessRequestNode,
    ) -> None:
        self.state = state
        self.greeting_node = greeting_node
        self.clarify_request_node = clarify_request_node
        self.schedule_meeting_node = schedule_meeting_node
        self.process_request_node = process_request_node

    def build(self) -> StateGraph:
        graph_builder = StateGraph(self.state)
        graph_builder.add_node(self.greeting_node.node_name, self.greeting_node.node_action)
        graph_builder.add_node(self.clarify_request_node.node_name, self.clarify_request_node.node_action)
        graph_builder.add_node(self.schedule_meeting_node.node_name, self.schedule_meeting_node.node_action)
        graph_builder.add_node(self.process_request_node.node_name, self.process_request_node.node_action)

        graph_builder.add_edge(START, self.clarify_request_node.node_name)
        # add conditional route
        graph_builder.add_conditional_edges(
            self.clarify_request_node.node_name,
            self.clarify_request_node.node_action,
            self.clarify_request_node.node_name,
            self.clarify_request_node.node_name,
        )
        
        
        



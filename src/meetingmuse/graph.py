"""
MeetingMuse LangGraph Workflow
"""

from langgraph.graph import StateGraph, START, END

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.services.routing_service import ConversationRouter


class GraphBuilder:
    def __init__(self, 
        state: MeetingMuseBotState,
        greeting_node: GreetingNode,
        clarify_request_node: ClarifyRequestNode,
        collecting_info_node: CollectingInfoNode,
        classify_intent_node: ClassifyIntentNode,
        conversation_router: ConversationRouter,
    ) -> None:
        self.state = state
        self.greeting_node = greeting_node
        self.clarify_request_node = clarify_request_node
        self.collecting_info_node = collecting_info_node
        self.classify_intent_node = classify_intent_node
        self.conversation_router = conversation_router

    def build(self) -> StateGraph:
        graph_builder = StateGraph(self.state)
        graph_builder.add_node(self.greeting_node.node_name, self.greeting_node.node_action)
        graph_builder.add_node(self.classify_intent_node.node_name, self.classify_intent_node.node_action)
        graph_builder.add_node(self.clarify_request_node.node_name, self.clarify_request_node.node_action)
        graph_builder.add_node(self.collecting_info_node.node_name, self.collecting_info_node.node_action)

        graph_builder.add_edge(START, self.classify_intent_node.node_name)
        # add conditional route using the routing service
        graph_builder.add_conditional_edges(
            self.classify_intent_node.node_name,
            self.conversation_router.intent_to_node_name_router,
            {
                NodeName.GREETING: NodeName.GREETING,
                NodeName.COLLECTING_INFO: NodeName.COLLECTING_INFO,
                NodeName.CLARIFY_REQUEST: NodeName.CLARIFY_REQUEST,
            }
        )
        graph_builder.add_conditional_edges(
            self.collecting_info_node.node_name,
            self.collecting_info_node.get_next_node_name,
            {
                NodeName.COLLECTING_INFO: NodeName.COLLECTING_INFO,
                NodeName.END: END,
            }
        )
        # Add edges to END for completion
        graph_builder.add_edge(self.greeting_node.node_name, END)
        graph_builder.add_edge(self.clarify_request_node.node_name, END)
        
        return graph_builder.compile()
    
    def draw_graph(self) -> None:
        try:
            graph = self.build()
            with open("graph.png", "wb") as f:
                f.write(graph.get_graph().draw_mermaid_png())
            print("Graph saved as graph.png")
        except Exception as e:
            print(f"Could not generate graph: {e}")
            raise e
        
        
        



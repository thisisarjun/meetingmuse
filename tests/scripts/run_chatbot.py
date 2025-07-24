from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from meetingmuse.nodes import clarify_request_node, collecting_info_node, classify_intent_node, greeting_node
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.graph import GraphBuilder
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.nodes.collecting_info_node import CollectingInfoNode
from meetingmuse.nodes.clarify_request_node import ClarifyRequestNode

logger = Logger()
conversation_router = ConversationRouter(logger)
model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
intent_classifier = IntentClassifier(model)
classify_intent_node = ClassifyIntentNode(intent_classifier)
greeting_node = GreetingNode(model)
collecting_info_node = CollectingInfoNode(model, logger)
clarify_request_node = ClarifyRequestNode(model)

class ChatBot:
    def __init__(self, graph):
        self.graph = graph
        self.thread_id = "conversation_1"
        self.config = {"configurable": {"thread_id": self.thread_id}}
    
    def process_input(self, user_input: str):
        # Always add the user message and process
        input_data = {"messages": [HumanMessage(content=user_input)]}
        
        for events in self.graph.stream(
            input_data, 
            config=self.config,
            stream_mode="values"
        ):
            messages = events["messages"]
            message = messages[-1]
            if message and message.type == "ai" and message.content:
                print("Assistant:", message.content)
        
        # Check if we're interrupted and waiting for more input
        current_state = self.graph.get_state(self.config)
        if current_state and current_state.next:
            print(f"[System: Waiting for your input, will resume at {current_state.next}]")



if __name__ == "__main__":
    graph_builder = GraphBuilder(
        state=MeetingMuseBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        collecting_info_node=collecting_info_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
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
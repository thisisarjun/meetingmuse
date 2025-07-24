from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
from meetingmuse.models.node import NodeName
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.models.state import CalendarBotState, ConversationStep, UserIntent
from meetingmuse.nodes.base_node import BaseNode


class ClassifyIntentNode(BaseNode):
    

    def __init__(self, intent_classifier: IntentClassifier):
        self.intent_classifier = intent_classifier
    
    def get_current_step(self, user_intent: UserIntent) -> ConversationStep:
        if user_intent == UserIntent.SCHEDULE_MEETING:
            return ConversationStep.COLLECTING_INFO
        elif user_intent in [UserIntent.CHECK_AVAILABILITY, UserIntent.CANCEL_MEETING, UserIntent.RESCHEDULE_MEETING]:
            return ConversationStep.PROCESSING_REQUEST
        elif user_intent == UserIntent.UNKNOWN:
            return ConversationStep.CLARIFYING_REQUEST
        elif user_intent == UserIntent.GENERAL_CHAT:
            return ConversationStep.GREETING
        else:
            raise ValueError(f"Unknown user intent: {user_intent}")
        

    def node_action(self, state: CalendarBotState) -> CalendarBotState:
        last_message = state["messages"][-1]

        if isinstance(last_message, HumanMessage):
            intent = self.intent_classifier.classify(last_message.content)
            state["user_intent"] = intent
            state["current_step"] = self.get_current_step(intent)

        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.CLASSIFY_INTENT







    

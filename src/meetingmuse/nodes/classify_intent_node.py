from langchain_core.messages import HumanMessage
from meetingmuse.models.node import NodeName
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode


class ClassifyIntentNode(BaseNode):
    

    def __init__(self, intent_classifier: IntentClassifier):
        self.intent_classifier = intent_classifier

        

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        last_message = state.messages[-1]

        if isinstance(last_message, HumanMessage):
            intent = self.intent_classifier.classify(last_message.content)
            state.user_intent = intent

        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.CLASSIFY_INTENT

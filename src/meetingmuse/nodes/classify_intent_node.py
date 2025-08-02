from langchain_core.messages import BaseMessage, HumanMessage

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.services.intent_classifier import IntentClassifier


class ClassifyIntentNode(BaseNode):
    intent_classifier: IntentClassifier

    def __init__(self, intent_classifier: IntentClassifier) -> None:
        self.intent_classifier = intent_classifier

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        last_message: BaseMessage = state.messages[-1]

        if isinstance(last_message, HumanMessage):
            # Handle both string and complex content types
            content = last_message.content
            if isinstance(content, str):
                message_text = content
            else:
                message_text = str(content)

            intent: UserIntent = self.intent_classifier.classify(message_text)
            state.user_intent = intent

        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.CLASSIFY_INTENT

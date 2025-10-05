from langchain_core.messages import BaseMessage, HumanMessage

from common.decorators import log_node_entry
from common.logger import Logger
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, UserIntent
from meetingmuse.nodes.base_node import SyncNode
from meetingmuse.services.intent_classifier import IntentClassifier


class ClassifyIntentNode(SyncNode):
    intent_classifier: IntentClassifier

    def __init__(self, intent_classifier: IntentClassifier, logger: Logger) -> None:
        super().__init__(logger)
        self.intent_classifier = intent_classifier

    @log_node_entry(NodeName.CLASSIFY_INTENT)
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

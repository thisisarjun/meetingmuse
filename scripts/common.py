from typing import Any

from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
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
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.services.meeting_details_service import MeetingDetailsService
from meetingmuse.services.routing_service import ConversationRouter
from meetingmuse.utils.logger import Logger


def initialize_nodes() -> dict[str, Any]:
    logger = Logger()
    model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
    intent_classifier = IntentClassifier(model)
    classify_intent_node = ClassifyIntentNode(intent_classifier, logger)
    greeting_node = GreetingNode(model, logger)
    collecting_info_node = CollectingInfoNode(model, logger)
    clarify_request_node = ClarifyRequestNode(model, logger)
    meeting_details_service = MeetingDetailsService(model, logger)
    human_schedule_meeting_more_info_node = HumanScheduleMeetingMoreInfoNode(logger)
    prompt_missing_meeting_details_node = PromptMissingMeetingDetailsNode(
        meeting_details_service, logger
    )
    schedule_meeting_node = ScheduleMeetingNode(model, logger)
    human_interrupt_retry_node = HumanInterruptRetryNode(logger)
    end_node = EndNode(logger)

    return {
        "conversation_router": ConversationRouter(logger),
        "model": model,
        NodeName.CLASSIFY_INTENT: classify_intent_node,
        NodeName.GREETING: greeting_node,
        NodeName.COLLECTING_INFO: collecting_info_node,
        NodeName.CLARIFY_REQUEST: clarify_request_node,
        NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO: human_schedule_meeting_more_info_node,
        NodeName.PROMPT_MISSING_MEETING_DETAILS: prompt_missing_meeting_details_node,
        NodeName.SCHEDULE_MEETING: schedule_meeting_node,
        NodeName.HUMAN_INTERRUPT_RETRY: human_interrupt_retry_node,
        NodeName.END: end_node,
    }

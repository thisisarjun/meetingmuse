
from enum import StrEnum

class NodeName(StrEnum):
    CLARIFY_REQUEST = "clarify_request"
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    CLASSIFY_INTENT = "classify_intent"
    SCHEDULE_MEETING = "api_call"
    HUMAN_INTERRUPT_RETRY = "human_interrupt_retry"
    END = "end"
    



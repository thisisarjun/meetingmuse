
from enum import StrEnum

class NodeName(StrEnum):
    CLARIFY_REQUEST = "clarify_request"
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    CLASSIFY_INTENT = "classify_intent"
    SCHEDULE_MEETING = "schedule_meeting"
    HUMAN_INTERRUPT_RETRY = "human_interrupt_retry"
    END = "end"
    
    # Human nodes
    HUMAN_SCHEDULE_MEETING_MORE_INFO = "human_schedule_meeting_more_info"
    



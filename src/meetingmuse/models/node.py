
from enum import StrEnum

class NodeName(StrEnum):
    CLARIFY_REQUEST = "clarify_request"
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    SCHEDULE_MEETING = "schedule_meeting"
    CLASSIFY_INTENT = "classify_intent"
    END = "end"
    
    # Human nodes
    HUMAN_SCHEDULE_MEETING_MORE_INFO = "human_schedule_meeting_more_info"
    



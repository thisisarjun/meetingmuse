
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

    # Prompt Nodes
    # Nodes are mainly used as a precursor to human nodes( mainly for prompting the user for missing information)
    PROMPT_MISSING_MEETING_DETAILS = "prompt_missing_meeting_details"
    



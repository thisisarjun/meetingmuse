from typing import Literal, Optional, Dict, Any, Union
from langchain_core.messages import HumanMessage, AIMessage

from meetingmuse.models.state import MeetingMuseBotState


class Utils:
       
    @staticmethod
    def is_last_message_human(state: MeetingMuseBotState) -> bool:
        return isinstance(state.messages[-1], HumanMessage)
    
    @staticmethod
    def is_last_message_ai(state: MeetingMuseBotState) -> bool:
        return isinstance(state.messages[-1], AIMessage)
    
    @staticmethod
    def get_last_message(state: MeetingMuseBotState, type: Literal["human", "ai"]) -> Optional[str]:

        last_message: Optional[str] = None
        for message in reversed(state.messages):
            if type == "human" and isinstance(message, HumanMessage):
                # Handle both string and complex content types
                content = message.content
                if isinstance(content, str):
                    last_message = content
                else:
                    last_message = str(content)
                break
            elif type == "ai" and isinstance(message, AIMessage):
                # Handle both string and complex content types
                content = message.content
                if isinstance(content, str):
                    last_message = content
                else:
                    last_message = str(content)
                break
        return last_message

    
    @staticmethod
    def get_last_message_from_events(events: Dict[str, Any], type: Literal["human", "ai"]) -> Optional[str]:
        last_message: Optional[str] = None
        for node_name, state in events.items():
            assert isinstance(state, MeetingMuseBotState), f"State for node {node_name} is not a MeetingMuseBotState"
            if state.messages:
                for message in reversed(state.messages):
                    if type == "human" and isinstance(message, HumanMessage):
                        # Handle both string and complex content types
                        content = message.content
                        if isinstance(content, str):
                            last_message = content
                        else:
                            last_message = str(content)
                        break
                    elif type == "ai" and isinstance(message, AIMessage):
                        # Handle both string and complex content types
                        content = message.content
                        if isinstance(content, str):
                            last_message = content
                        else:
                            last_message = str(content)
                        break
        return last_message
        
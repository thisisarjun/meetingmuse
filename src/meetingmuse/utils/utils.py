from typing import Literal, Optional
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

        last_message = None
        for message in reversed(state.messages):
            if type == "human" and isinstance(message, HumanMessage):
                last_message = message.content
                break
            elif type == "ai" and isinstance(message, AIMessage):
                last_message = message.content
                break
        return last_message

    
    @staticmethod
    def get_last_message_from_events(events: dict, type: Literal["human", "ai"]) -> Optional[str]:
        last_message = None
        for node_name, state in events.items():
            assert isinstance(state, MeetingMuseBotState), f"State for node {node_name} is not a MeetingMuseBotState"
            if state.messages:
                for message in reversed(state.messages):
                    if type == "human" and isinstance(message, HumanMessage):
                        last_message = message.content
                        break
                    elif type == "ai" and isinstance(message, AIMessage):
                        last_message = message.content
                        break
        return last_message
        
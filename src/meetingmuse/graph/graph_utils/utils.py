from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import StateSnapshot

from meetingmuse.models.graph import MessageType
from meetingmuse.models.interrupts import InterruptInfo
from meetingmuse.models.state import MeetingMuseBotState


class Utils:
    @staticmethod
    def is_last_message_human(state: MeetingMuseBotState) -> bool:
        return isinstance(state.messages[-1], HumanMessage)

    @staticmethod
    def is_last_message_ai(state: MeetingMuseBotState) -> bool:
        return isinstance(state.messages[-1], AIMessage)

    @staticmethod
    def get_last_message(
        state: MeetingMuseBotState, input_type: MessageType
    ) -> Optional[str]:
        last_message: Optional[str] = None
        for message in reversed(state.messages):
            if input_type == MessageType.HUMAN and message.type == MessageType.HUMAN:
                # Handle both string and complex content types
                content = message.content
                if isinstance(content, str):
                    last_message = content
                else:
                    last_message = str(content)
                break
            if input_type == MessageType.AI and message.type == MessageType.AI:
                # Handle both string and complex content types
                content = message.content
                if isinstance(content, str):
                    last_message = content
                else:
                    last_message = str(content)
                break
        return last_message

    @staticmethod
    def get_last_message_from_events(
        events: Dict[str, Any], input_type: MessageType
    ) -> Optional[str]:
        last_message: Optional[str] = None
        for _, state in events.items():
            meeting_muse_bot_state = MeetingMuseBotState.model_validate(state)
            if meeting_muse_bot_state.messages:
                for message in reversed(meeting_muse_bot_state.messages):
                    if (
                        input_type == MessageType.HUMAN
                        and message.type == MessageType.HUMAN
                    ):
                        # Handle both string and complex content types
                        content = message.content
                        if isinstance(content, str):
                            last_message = content
                        else:
                            last_message = str(content)
                        break
                    if input_type == MessageType.AI and message.type == MessageType.AI:
                        # Handle both string and complex content types
                        content = message.content
                        if isinstance(content, str):
                            last_message = content
                        else:
                            last_message = str(content)
                        break
        return last_message

    @staticmethod
    def get_interrupt_info_from_events(
        events: Dict[str, Any]
    ) -> Optional[InterruptInfo]:
        if "__interrupt__" in events:
            interrupt_info = events["__interrupt__"][0].value

            assert isinstance(interrupt_info, InterruptInfo)
            return interrupt_info
        return None

    @staticmethod
    def get_interrupt_info_from_state_snapshot(
        state: StateSnapshot,
    ) -> Optional[InterruptInfo]:
        if state.interrupts:
            interrupt_info = state.interrupts[0].value
            assert isinstance(interrupt_info, InterruptInfo)
            return interrupt_info
        return None

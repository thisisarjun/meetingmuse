from abc import ABC, abstractmethod

from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState

class BaseNode(ABC):
    @abstractmethod
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        raise NotImplementedError(
            f"Node action not implemented for {self.__class__.__name__}"
        )

    @property
    @abstractmethod
    def node_name(self) -> NodeName:
        raise NotImplementedError(
            f"Node name not implemented for {self.__class__.__name__}"
        )    
from abc import ABC, abstractmethod
from typing import Union

from langgraph.types import Command

from common.logger import Logger
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState


class BaseNode(ABC):
    def __init__(self, logger: Logger):
        self.logger = logger
        self.logger.set_prefix(self.node_name.value)

    @property
    @abstractmethod
    def node_name(self) -> NodeName:
        raise NotImplementedError(
            f"Node name not implemented for {self.__class__.__name__}"
        )


class SyncNode(BaseNode):
    @abstractmethod
    def node_action(
        self, state: MeetingMuseBotState
    ) -> Union[MeetingMuseBotState, Command]:
        raise NotImplementedError(
            f"Node action not implemented for {self.__class__.__name__}"
        )


class AsyncNode(BaseNode):
    @abstractmethod
    async def node_action(
        self, state: MeetingMuseBotState
    ) -> Union[MeetingMuseBotState, Command]:
        raise NotImplementedError(
            f"Node action not implemented for {self.__class__.__name__}"
        )


__all__ = ["SyncNode", "AsyncNode"]

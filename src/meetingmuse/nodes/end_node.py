from common.decorators.log_decorator import log_node_entry
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode


class EndNode(BaseNode):
    """
    This node will be the final node before reaching END
    """

    @log_node_entry(NodeName.END)
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        # revert the state to initial state
        state = MeetingMuseBotState()
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.END

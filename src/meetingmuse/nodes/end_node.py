from common.decorators import log_node_entry
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState, OperationStatus
from meetingmuse.nodes.base_node import SyncNode


class EndNode(SyncNode):
    """
    This node will be the final node before reaching END
    """

    @log_node_entry(NodeName.END)
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        # revert the meeting details to original state
        state.meeting_details = MeetingFindings()
        state.user_intent = None
        state.operation_status = OperationStatus()
        state.setup_human_input = False
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.END

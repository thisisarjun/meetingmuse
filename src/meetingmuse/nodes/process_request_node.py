from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName


class ProcessRequestNode(BaseNode):

    def __init__(self):
        pass

    def node_action(self, _state: MeetingMuseBotState) -> MeetingMuseBotState:
        # TODO: Implement this node
        return _state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.PROCESS_REQUEST
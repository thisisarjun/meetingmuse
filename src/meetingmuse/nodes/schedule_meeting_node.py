from langchain_core.messages import HumanMessage, AIMessage
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState, ConversationStep
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from meetingmuse.prompts.schedule_meeting_prompt import SCHEDULE_MEETING_PROMPT
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.meeting import MeetingFindings

class ScheduleMeetingNode(BaseNode):

    def __init__(self, model: HuggingFaceModel):
        self.model = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SCHEDULE_MEETING_PROMPT),
            ("user", "{user_message}"),
        ])
        self.parser = PydanticOutputParser(pydantic_object=MeetingFindings)
        self.chain = self.prompt | self.model.chat_model | self.parser

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:

        last_human_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                last_human_message = message
                break

        if last_human_message:
            response = self.chain.invoke({"user_message": last_human_message.content})
            state["messages"].append(AIMessage(content=response.model_dump_json()))
            state["current_step"] = ConversationStep.COLLECTING_INFO
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING
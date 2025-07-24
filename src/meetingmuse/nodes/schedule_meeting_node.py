from langchain_core.messages import HumanMessage, AIMessage
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState, ConversationStep
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from meetingmuse.prompts.schedule_meeting_prompt import SCHEDULE_MEETING_PROMPT
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.utils.logger import Logger

class ScheduleMeetingNode(BaseNode):

    def __init__(self, model: HuggingFaceModel, logger: Logger):
        self.model = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SCHEDULE_MEETING_PROMPT),
            ("user", "{user_message}"),
        ])
        self.parser = PydanticOutputParser(pydantic_object=MeetingFindings)
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.logger = logger

    def is_meeting_details_complete(self, meeting_details: MeetingFindings) -> bool:
        # check if title, participants, date_time and duration are not null
        return all(meeting_details.title is not None,
                   meeting_details.participants is not None,
                   meeting_details.date_time is not None,
                   meeting_details.duration is not None)

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:

        last_human_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                last_human_message = message
                break
        
        if not last_human_message:
            return state
        
        meeting_details = state["meeting_details"]

        if meeting_details is None:
            response = self.chain.invoke({"user_message": last_human_message.content})        
            self.logger.info(f"Schedule meeting node response: {response}")
            state["messages"].append(AIMessage(content=response.model_dump_json()))
            state["current_step"] = ConversationStep.COLLECTING_INFO
            return state

        if self.is_meeting_details_complete(meeting_details):
            # TODO: schedule the actual meeting            
            response = f"Perfect! I'll schedule your meeting '{meeting_details.title}' " \
                      f"for {meeting_details.date_time} with {meeting_details.participants}."            
            state["messages"].append(AIMessage(content=response))
            state["current_step"] = ConversationStep.COMPLETED            
            return state
        

        response = self.chain.invoke({"user_message": last_human_message.content})        
        self.logger.info(f"Schedule meeting node response: {response}")
        state["messages"].append(AIMessage(content=response.model_dump_json()))
        state["current_step"] = ConversationStep.COLLECTING_INFO
        return state
    @property
    def node_name(self) -> NodeName:
        return NodeName.SCHEDULE_MEETING
from langchain_core.messages import HumanMessage, AIMessage
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState, ConversationStep
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from meetingmuse.prompts.schedule_meeting_prompt import SCHEDULE_MEETING_PROMPT
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.utils.logger import Logger

class CollectingInfoNode(BaseNode):

    def __init__(self, model: HuggingFaceModel, logger: Logger):
        self.model = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SCHEDULE_MEETING_PROMPT),
        ])
        self.parser = StrOutputParser()
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.logger = logger

    def is_meeting_details_complete(self, meeting_details: MeetingFindings) -> bool:
        # check if title and date_time are present (minimum required)
        return all([
            meeting_details.title is not None,
            meeting_details.date_time is not None
        ])

    def get_missing_fields(self, meeting_details: MeetingFindings) -> list[str]:
        missing = []
        if not meeting_details.title:
            missing.append("title")
        if not meeting_details.date_time:
            missing.append("time")
        if not meeting_details.participants:
            missing.append("participants")
        return missing

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:

        last_human_message = None
        for message in reversed(state.messages):
            if isinstance(message, HumanMessage):
                last_human_message = message
                break
        
        if not last_human_message:
            return state
        
        meeting_details = state.meeting_details
        current_details = meeting_details.model_dump() if meeting_details else {}
        missing_fields = self.get_missing_fields(meeting_details)

        if self.is_meeting_details_complete(meeting_details):
            # TODO: schedule the actual meeting            
            response = f"Perfect! I'll schedule your meeting '{meeting_details.title}' " \
                      f"for {meeting_details.date_time}"
            if meeting_details.participants:
                response += f" with {', '.join(meeting_details.participants)}"
            response += ". Your meeting is confirmed!"
            
            state.messages.append(AIMessage(content=response))
            return state
        

        response = self.chain.invoke({
            "user_message": last_human_message.content,
            "current_details": current_details,
            "missing_fields": ", ".join(missing_fields) if missing_fields else "none"
        })        
        self.logger.info(f"Schedule meeting node response: {response}")
        state.messages.append(AIMessage(content=response))
        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.COLLECTING_INFO
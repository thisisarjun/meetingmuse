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

class CollectingInfoNode(BaseNode):
    """
    Collecting Info node specific for scheduling a meeting.
    This node is responsible for collecting information from the user.
    It is used to collect the meeting details from the user.
    """
    def __init__(self, model: HuggingFaceModel, logger: Logger):
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=MeetingFindings)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SCHEDULE_MEETING_PROMPT),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.logger = logger

    def is_meeting_details_complete(self, meeting_details: MeetingFindings) -> bool:
        # check if title and date_time are present (minimum required)
        return all([
            meeting_details.title is not None,
            meeting_details.date_time is not None
        ])

    def get_next_node_name(self, state: MeetingMuseBotState) -> NodeName:
        if state.meeting_details and self.is_meeting_details_complete(state.meeting_details):
            return NodeName.END
        return NodeName.COLLECTING_INFO
    
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
            response = f"Perfect! I'll schedule your meeting '{meeting_details.title}' " \
                      f"for {meeting_details.date_time}"
            if meeting_details.participants:
                response += f" with {', '.join(meeting_details.participants)}"            
            state.messages.append(AIMessage(content=response))
            return state
        

        updated_meeting_details = self.chain.invoke({
            "user_message": last_human_message.content,
            "current_details": current_details,
            "missing_fields": ", ".join(missing_fields) if missing_fields else "none",
            "format_instructions": self.parser.get_format_instructions()
        })        
        
        # Update the state with the parsed meeting details
        state.meeting_details = updated_meeting_details
        self.logger.info(f"Updated meeting details: {updated_meeting_details}")
        
        # Generate a conversational response
        response = "I've updated your meeting details. Let me know if you need any changes!"
        state.messages.append(AIMessage(content=response))
        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.COLLECTING_INFO
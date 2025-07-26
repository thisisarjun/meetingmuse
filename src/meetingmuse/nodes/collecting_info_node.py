from langchain_core.messages import HumanMessage, AIMessage
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from meetingmuse.prompts.schedule_meeting_collecting_info_prompt import SCHEDULE_MEETING_COLLECTING_INFO_PROMPT
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName
from meetingmuse.models.meeting import MeetingFindings
from meetingmuse.services.meeting_details_service import MeetingDetailsService
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
            ("system", SCHEDULE_MEETING_COLLECTING_INFO_PROMPT),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.logger = logger
        self.meeting_service = MeetingDetailsService(model, logger)

    def get_next_node_name(self, state: MeetingMuseBotState) -> NodeName:
        self.logger.info(f"Getting next node name: {state.meeting_details}")
        if state.meeting_details and self.meeting_service.is_meeting_details_complete(state.meeting_details):
            self.logger.info(f"Meeting details are complete, returning to END")
            return NodeName.END
        self.logger.info(f"Meeting details are not complete, returning to COLLECTING_INFO")
        return NodeName.COLLECTING_INFO

    def complete_state(self, meeting_details: MeetingFindings, state: MeetingMuseBotState) -> MeetingMuseBotState:
        """Complete the state with the missing required fields"""
        response = self.meeting_service.generate_completion_message(meeting_details)
        state.messages.append(AIMessage(content=response))
        return state

    def invoke_extraction_prompt(self, meeting_details: MeetingFindings, missing_required: list[str], user_input: str) -> MeetingFindings:
        """Invoke the extraction prompt to get the missing required fields"""
        return self.chain.invoke({
            "user_message": user_input,
            "current_details": meeting_details.model_dump(),
            "missing_fields": ", ".join(missing_required) if missing_required else "none",
            "format_instructions": self.parser.get_format_instructions()
        })
    
    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:

        # TODO: make this a helper method in utils.py
        last_human_message = None
        for message in reversed(state.messages):
            if isinstance(message, HumanMessage):
                last_human_message = message.content
                break
        
        if not last_human_message:
            return state
        
        meeting_details = state.meeting_details or MeetingFindings()
        self.logger.info(f"Meeting details: {meeting_details}")
        missing_required = self.meeting_service.get_missing_required_fields(meeting_details)

        if self.meeting_service.is_meeting_details_complete(meeting_details):
            return self.complete_state(meeting_details, state)        

        try:
            new_meeting_details = self.invoke_extraction_prompt(meeting_details, missing_required, last_human_message)
        except Exception as e:
            self.logger.error(f"Parsing error: {e}")
            # Fallback: keep existing details
            new_meeting_details = meeting_details
        
        # Update only non None fields
        state = self.meeting_service.update_state_meeting_details(new_meeting_details, state)
        
        self.logger.info(f"Updated meeting details: {state.meeting_details}")
        
        # Generate contextual response based on missing required fields
        updated_missing_required = self.meeting_service.get_missing_required_fields(state.meeting_details)
        
        if updated_missing_required:
            try:
                response = self.meeting_service.invoke_missing_fields_prompt(state).content
            except Exception as e:
                self.logger.error(f"Missing fields prompt error: {e}")
                response = "I need some more information to schedule your meeting. Could you provide the missing details?"
        else:
            response = "Great! I have all the information I need."
        
        state.messages.append(AIMessage(content=response))
        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.COLLECTING_INFO
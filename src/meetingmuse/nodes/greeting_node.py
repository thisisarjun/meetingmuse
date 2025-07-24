from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState, ConversationStep, UserIntent
from meetingmuse.prompts.greeting_prompt import GREETING_PROMPT
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.models.node import NodeName

class GreetingNode(BaseNode):

    def __init__(self, model: HuggingFaceModel):
        self.model = model
        self.parser = StrOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", GREETING_PROMPT),
            ("user", "user message: {user_message}"),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        last_human_message = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                last_human_message = message
                break

        if last_human_message:
            response = self.chain.invoke({"user_message": last_human_message.content})
            state["messages"].append(AIMessage(content=response))
            state["current_step"] = ConversationStep.COMPLETED

        return state
    
    @property
    def node_name(self) -> NodeName:
        return NodeName.GREETING
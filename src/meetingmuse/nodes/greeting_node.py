from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import CalendarBotState, ConversationStep, UserIntent

class GreetingNode:

    PROMPT = """

        You are CalendarBot, a friendly meeting scheduler assistant.
            
        The user just greeted you. Respond warmly and briefly explain how you can help:
        - Schedule new meetings
        - Check calendar availability  
        - Cancel or reschedule existing meetings

        Keep it conversational and welcoming. Don't be too wordy.
    """

    def __init__(self, model: HuggingFaceModel):
        self.model = model
        self.parser = StrOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT),
            ("user", "user message: {user_message}"),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser

    def __call__(self, state: CalendarBotState) -> CalendarBotState:
        
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
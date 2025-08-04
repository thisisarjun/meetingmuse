from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.base_node import BaseNode
from meetingmuse.prompts.clarify_request_prompt import CLARIFY_REQUEST_PROMPT


class ClarifyRequestNode(BaseNode):
    model: HuggingFaceModel
    prompt: ChatPromptTemplate
    parser: StrOutputParser
    chain: Runnable[Dict[str, Any], str]

    def __init__(self, model: HuggingFaceModel) -> None:
        self.model = model
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CLARIFY_REQUEST_PROMPT),
                ("user", "user message: {user_message}"),
            ]
        )
        self.parser = StrOutputParser()
        self.chain = self.prompt | self.model.chat_model | self.parser

    def node_action(self, state: MeetingMuseBotState) -> MeetingMuseBotState:
        last_human_message: Optional[HumanMessage] = None
        for message in reversed(state.messages):
            if isinstance(message, HumanMessage):
                last_human_message = message
                break

        if last_human_message:
            response: str = self.chain.invoke(
                {"user_message": last_human_message.content}
            )
            state.messages.append(AIMessage(content=response))
        return state

    @property
    def node_name(self) -> NodeName:
        return NodeName.CLARIFY_REQUEST

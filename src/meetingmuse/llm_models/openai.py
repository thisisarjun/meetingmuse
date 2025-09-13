from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from common.config import config
from meetingmuse.llm_models.base import BaseLlmModel


class OpenAIModel(BaseLlmModel):
    model_name: str

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @property
    def chat_model(self) -> BaseChatModel:
        return ChatOpenAI(model=self.model_name, api_key=config.OPENAI_API_KEY)

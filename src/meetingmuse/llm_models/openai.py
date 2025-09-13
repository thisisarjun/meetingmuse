from langchain_openai import ChatOpenAI

from common.config import config


class OpenAIModel:
    model_name: str

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def chat_model(self) -> ChatOpenAI:
        return ChatOpenAI(model=self.model_name, api_key=config.OPENAI_API_KEY)

from langchain_core.language_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from common.config import config
from meetingmuse.llm_models.base import BaseLlmModel


class HuggingFaceModel(BaseLlmModel):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @property
    def chat_model(self) -> BaseChatModel:
        return ChatHuggingFace(
            llm=HuggingFaceEndpoint(  # type: ignore[call-arg]
                repo_id=self.model_name,
                huggingfacehub_api_token=config.HUGGINGFACE_API_TOKEN,
            )
        )

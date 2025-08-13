from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from ..config.config import config


class HuggingFaceModel:
    model_name: str
    llm: HuggingFaceEndpoint

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.llm = HuggingFaceEndpoint(
            repo_id=self.model_name,
            huggingfacehub_api_token=config.HUGGINGFACE_API_TOKEN,
        )

    @property
    def chat_model(self) -> ChatHuggingFace:
        return ChatHuggingFace(llm=self.llm)

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from ..config.config import config

class HuggingFaceModel:

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.llm = HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=config.HUGGINGFACE_API_TOKEN,
        )
    
    @property
    def chat_model(self):
        return ChatHuggingFace(
            llm=self.llm
        )







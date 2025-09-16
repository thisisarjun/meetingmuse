from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class BaseLlmModel(ABC):
    model_name: str

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @property
    @abstractmethod
    def chat_model(self) -> BaseChatModel:
        raise NotImplementedError("Subclasses must implement this method")

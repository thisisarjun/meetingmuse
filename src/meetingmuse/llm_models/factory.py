from meetingmuse.llm_models.base import BaseLlmModel
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.llm_models.openai import OpenAIModel


def create_llm_model(model_name: str, provider: str = "huggingface") -> BaseLlmModel:
    if provider == "openai":
        return OpenAIModel(model_name)
    if provider == "huggingface":
        return HuggingFaceModel(model_name)
    raise ValueError(f"Invalid provider: {provider}")

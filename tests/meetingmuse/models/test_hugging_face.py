import pytest

from common.logger import Logger
from meetingmuse.llm_models.hugging_face import HuggingFaceModel


@pytest.mark.skip(reason="Real model test")
def test_hugging_face_model():
    logger = Logger("test_hugging_face")
    model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
    assert model.chat_model is not None
    result = model.chat_model.invoke("Hello, how are you?")
    logger.info(f"Model response: {result}")

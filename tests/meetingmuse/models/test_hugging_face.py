import pytest

from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.utils import Logger


@pytest.mark.skip(reason="Real model test")
def test_hugging_face_model():
    logger = Logger("test_hugging_face")
    model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
    assert model.chat_model is not None
    result = model.chat_model.invoke("Hello, how are you?")
    logger.info(f"Model response: {result}")

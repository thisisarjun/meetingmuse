from meetingmuse.llm_models.hugging_face import HuggingFaceModel

def test_hugging_face_model():
    model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
    assert model.chat_model is not None
    result = model.chat_model.invoke("Hello, how are you?")
    print(result)
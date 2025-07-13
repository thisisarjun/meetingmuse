import traceback
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import UserIntent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from meetingmuse.prompts import intent_classifier_prompt

class IntentClassifier:


    def __init__(self, model: HuggingFaceModel):
        self.model = model
        self.parser = StrOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", intent_classifier_prompt.SYSTEM_PROMPT),
            ("user", "user message: {user_message}"),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser

    def classify(self, user_message: str) -> UserIntent:
        try:
            result = self.chain.invoke({"user_message": user_message})
            return UserIntent(result)
        except Exception as e:
            print(f"Error classifying intent: {e}")
            print(f"Error type: {type(e)}")
            
            traceback.print_exc()
            return UserIntent.UNKNOWN
    
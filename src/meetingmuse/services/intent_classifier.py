import traceback
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import UserIntent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from meetingmuse.prompts import intent_classifier_prompt
from meetingmuse.utils import Logger

class IntentClassifier:

    def __init__(self, model: HuggingFaceModel):
        self.model = model
        self.parser = StrOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", intent_classifier_prompt.SYSTEM_PROMPT),
            ("user", "user message: {user_message}"),
        ])
        self.chain = self.prompt | self.model.chat_model | self.parser
        self.logger = Logger()

    def classify(self, user_message: str) -> UserIntent:
        try:
            result = self.chain.invoke({"user_message": user_message})
            return UserIntent(result)
        except Exception as e:
            self.logger.error(f"Error classifying intent: {e}")
            self.logger.error(f"Error type: {type(e)}")
            
            traceback.print_exc()
            return UserIntent.UNKNOWN
    
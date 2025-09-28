import pytest

from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import UserIntent
from meetingmuse.services.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Test suite for IntentClassifier with real Llama model integration."""

    @pytest.mark.parametrize(
        "user_message,expected_intent",
        [
            # Schedule meeting scenarios
            (
                "I need to schedule a meeting with my team for tomorrow at 2pm",
                UserIntent.SCHEDULE_MEETING,
            ),
            (
                "Book an appointment with the client next week",
                UserIntent.SCHEDULE_MEETING,
            ),
            ("Set up a call with the marketing team", UserIntent.SCHEDULE_MEETING),
            ("Can we arrange a meeting for Friday?", UserIntent.SCHEDULE_MEETING),
            # Reschedule meeting scenarios
            # General chat scenarios
            ("Hello there!", UserIntent.GENERAL_CHAT),
            ("Thank you for your help", UserIntent.GENERAL_CHAT),
            ("Good morning", UserIntent.GENERAL_CHAT),
            ("How are you doing?", UserIntent.GENERAL_CHAT),
        ],
    )
    @pytest.mark.skip(reason="Real model test")
    def test_classify_intent_happy_flow(
        self, user_message: str, expected_intent: UserIntent
    ):
        """
        Parameterized happy flow test: Tests various user intents.

        This test uses the actual Llama model to classify user intent
        for different types of requests.
        """
        # Arrange: Set up the classifier with Llama model
        llama_model = HuggingFaceModel("meta-llama/Meta-Llama-3-8B-Instruct")
        classifier = IntentClassifier(llama_model)

        # Act: Classify the user's intent
        result = classifier.classify(user_message)

        # Assert: Should correctly identify the expected intent
        assert (
            result == expected_intent
        ), f"Expected {expected_intent} but got {result} for message: '{user_message}'"
        assert isinstance(result, UserIntent)

        # Additional validation: Result should be a valid enum value
        assert result in [intent.value for intent in UserIntent]

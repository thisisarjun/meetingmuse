#!/usr/bin/env python3
"""
MeetingMuse CLI Entry Point
"""

from meetingmuse.graph import GraphBuilder
from meetingmuse.llm_models.hugging_face import HuggingFaceModel
from meetingmuse.models.state import MeetingMuseBotState
from meetingmuse.nodes.classify_intent_node import ClassifyIntentNode
from meetingmuse.nodes.greeting_node import GreetingNode
from meetingmuse.services.intent_classifier import IntentClassifier
from meetingmuse.utils import Logger


def main() -> None:
    """Main entry point for the MeetingMuse CLI."""
    logger: Logger = Logger()
    logger.info("Welcome to MeetingMuse - Your favourite calendar bot!")
    # TODO: Implement CLI interface


if __name__ == "__main__":
    main()

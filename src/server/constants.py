"""
WebSocket Server Constants
Defines error codes, message types, and other constants for the MeetingMuse WebSocket server
"""
from enum import StrEnum


# Error Codes for Error Messages
class ErrorCodes(StrEnum):
    """Error codes sent in error messages to clients"""

    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    LLM_PROCESSING_ERROR = "LLM_PROCESSING_ERROR"


# Error Messages
class ErrorMessages(StrEnum):
    """Human-readable error messages corresponding to error codes"""

    INVALID_MESSAGE_FORMAT = (
        "Message format is invalid. Please check the message structure."
    )
    INTERNAL_SERVER_ERROR = "An internal error occurred. Please try reconnecting."
    LLM_PROCESSING_ERROR = (
        "I'm having trouble processing your request. Please try again."
    )


# System Message Types
class SystemMessageTypes(StrEnum):
    """Types of system messages sent to clients"""

    CONNECTION_ESTABLISHED = "connection_established"
    PROCESSING = "processing"
    CONVERSATION_RESUMED = "conversation_resumed"
    WAITING_FOR_INPUT = "waiting_for_input"
    PROCESSING_STEP = "processing_step"


# WebSocket Close Reasons
class CloseReasons(StrEnum):
    """Human-readable reasons for WebSocket connection closures"""

    CONNECTION_ESTABLISHMENT_FAILED = "Failed to establish connection"

"""
WebSocket Server Constants
Defines error codes, message types, and other constants for the MeetingMuse WebSocket server
"""


# WebSocket Close Codes
class WebSocketCloseCodes:
    """Standard WebSocket close codes"""

    POLICY_VIOLATION = 1008
    INTERNAL_ERROR = 1011


# Error Codes for Error Messages
class ErrorCodes:
    """Error codes sent in error messages to clients"""

    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


# Error Messages
class ErrorMessages:
    """Human-readable error messages corresponding to error codes"""

    INVALID_MESSAGE_FORMAT = (
        "Message format is invalid. Please check the message structure."
    )
    INTERNAL_SERVER_ERROR = "An internal error occurred. Please try reconnecting."


# System Message Types
class SystemMessageTypes:
    """Types of system messages sent to clients"""

    CONNECTION_ESTABLISHED = "connection_established"
    PROCESSING = "processing"


# WebSocket Close Reasons
class CloseReasons:
    """Human-readable reasons for WebSocket connection closures"""

    INVALID_CLIENT_ID = "Invalid client ID format"
    CONNECTION_ESTABLISHMENT_FAILED = "Failed to establish connection"

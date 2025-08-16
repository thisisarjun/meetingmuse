"""
Pydantic models for API request and response schemas
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Request model for messages"""

    content: str = Field(
        ...,
        description="Message content",
        min_length=1,
        max_length=1000,
        examples=["A sample message content"],
    )


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(..., description="When the error occurred")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class HealthStatus(BaseModel):
    """Health status model"""

    status: str = Field(..., description="Overall health status", examples=["healthy"])
    active_connections: int = Field()

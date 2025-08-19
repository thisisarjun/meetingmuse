"""
Pydantic models for API request and response schemas
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


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

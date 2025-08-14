"""
Pydantic models for API request and response schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

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


class BroadcastResponse(BaseModel):
    """Response model for broadcast operations"""

    success: bool = Field(..., description="Whether the broadcast was successful")
    message: str = Field(..., description="Status message")
    clients_notified: int = Field(
        ..., description="Number of clients that received the message"
    )
    timestamp: datetime = Field(..., description="When the broadcast was sent")


class ConnectionInfo(BaseModel):
    """Information about a single WebSocket connection"""

    client_id: str = Field(..., description="Unique client identifier")
    connected_at: datetime = Field(..., description="Connection timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    messages_sent: int = Field(..., description="Number of messages sent by client")
    messages_received: int = Field(
        ..., description="Number of messages received from client"
    )


class ConnectionsResponse(BaseModel):
    """Response model for connections information"""

    total_connections: int = Field(
        ..., description="Total number of active connections"
    )
    connections: List[ConnectionInfo] = Field(
        ..., description="List of active connections"
    )
    timestamp: datetime = Field(..., description="When the data was retrieved")


class SystemStatistics(BaseModel):
    """System statistics model"""

    total_connections: int = Field(..., description="Total active connections")
    total_messages: int = Field(..., description="Total messages processed")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    active_conversations: int = Field(..., description="Number of active conversations")
    timestamp: datetime = Field(..., description="When the statistics were collected")


class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""

    success: bool = Field(..., description="Whether the cleanup was successful")
    connections_closed: int = Field(
        ..., description="Number of connections that were closed"
    )
    conversations_cleared: int = Field(
        ..., description="Number of conversations that were cleared"
    )
    message: str = Field(..., description="Cleanup status message")
    timestamp: datetime = Field(..., description="When the cleanup was performed")


class HealthStatus(BaseModel):
    """Health status model"""

    status: str = Field(..., description="Overall health status", examples=["healthy"])
    timestamp: datetime = Field(..., description="Health check timestamp")


class SystemMetrics(BaseModel):
    """System metrics model"""

    health_status: str = Field(..., description="Overall health status")
    active_connections: int = Field(
        ..., description="Number of active WebSocket connections"
    )
    total_messages_processed: int = Field(..., description="Total messages processed")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    langgraph_status: str = Field(..., description="LangGraph processor status")
    streaming_handler_status: str = Field(..., description="Streaming handler status")
    timestamp: datetime = Field(..., description="When the metrics were collected")


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(..., description="When the error occurred")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

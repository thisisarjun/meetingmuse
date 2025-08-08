"""
Admin API
HTTP endpoints for administrative operations and management
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from ..models.api_dtos import (
    BroadcastResponse,
    CleanupResponse,
    ConnectionsResponse,
    ErrorResponse,
    MessageRequest,
    SystemStatistics,
)
from ..services.admin_service import AdminService

logger = logging.getLogger(__name__)


def create_admin_router(admin_service: AdminService) -> APIRouter:
    """Create and configure admin API router"""
    router = APIRouter(
        prefix="/admin",
        tags=["admin"],
        responses={
            401: {"model": ErrorResponse, "description": "Unauthorized"},
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
    )

    @router.post(  # type: ignore[misc]
        "/broadcast",
        response_model=BroadcastResponse,
        status_code=status.HTTP_200_OK,
        summary="Broadcast message to all clients",
        description="Send a message to all currently connected WebSocket clients",
        responses={
            400: {"model": ErrorResponse, "description": "Invalid message format"},
        },
    )
    async def broadcast_message(message: MessageRequest) -> BroadcastResponse:
        """
        Broadcast a message to all connected clients

        This endpoint allows administrators to send a message to all currently
        connected WebSocket clients. The message will be delivered as a system
        message to each active connection.

        - **content**: The message content to broadcast (1-1000 characters)
        """
        try:
            result = await admin_service.broadcast_message(message.content)
            return BroadcastResponse(
                success=True,
                message="Message broadcast successfully",
                clients_notified=result.get("clients_notified", 0),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to broadcast message",
            )

    @router.get(  # type: ignore[misc]
        "/connections",
        response_model=ConnectionsResponse,
        status_code=status.HTTP_200_OK,
        summary="Get active connections",
        description="Retrieve information about all currently active WebSocket connections",
    )
    async def get_connections() -> ConnectionsResponse:
        """
        Get information about active connections

        Returns detailed information about all currently active WebSocket connections,
        including connection timestamps, activity data, and message statistics.

        This endpoint is useful for monitoring connection health and user activity.
        """
        try:
            connections_info = admin_service.get_connections_info()
            return ConnectionsResponse(
                total_connections=connections_info.get("total_connections", 0),
                connections=connections_info.get("connections", []),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get connections info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve connections information",
            )

    @router.get(  # type: ignore[misc]
        "/statistics",
        response_model=SystemStatistics,
        status_code=status.HTTP_200_OK,
        summary="Get system statistics",
        description="Retrieve comprehensive system statistics for monitoring and admin dashboard",
    )
    async def get_system_statistics() -> SystemStatistics:
        """
        Get comprehensive system statistics

        Returns detailed system performance metrics including:
        - Connection statistics
        - Message processing metrics
        - Resource usage (CPU, memory)
        - Server uptime
        - Active conversation count

        This data is useful for system monitoring and performance analysis.
        """
        try:
            stats = admin_service.get_system_statistics()
            return SystemStatistics(
                total_connections=stats.get("total_connections", 0),
                total_messages=stats.get("total_messages", 0),
                uptime_seconds=stats.get("uptime_seconds", 0.0),
                memory_usage_mb=stats.get("memory_usage_mb", 0.0),
                cpu_usage_percent=stats.get("cpu_usage_percent", 0.0),
                active_conversations=stats.get("active_conversations", 0),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get system statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve system statistics",
            )

    @router.post(  # type: ignore[misc]
        "/cleanup",
        response_model=CleanupResponse,
        status_code=status.HTTP_200_OK,
        summary="Cleanup all connections",
        description="Forcefully close all active connections and clear conversation data (admin operation)",
    )
    async def cleanup_connections() -> CleanupResponse:
        """
        Clean up all active connections

        This is an administrative operation that forcefully closes all active
        WebSocket connections and clears associated conversation data.

        **Warning**: This will disconnect all users and should only be used
        for maintenance or emergency situations.

        Returns information about how many connections and conversations were cleaned up.
        """
        try:
            result = await admin_service.cleanup_connections()
            return CleanupResponse(
                success=result.get("success", False),
                connections_closed=result.get("connections_closed", 0),
                conversations_cleared=result.get("conversations_cleared", 0),
                message=result.get("message", "Cleanup completed"),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to cleanup connections: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cleanup connections",
            )

    return router

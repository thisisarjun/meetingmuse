"""
Health API
HTTP endpoints for system health checks and monitoring
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from ..models.api_dtos import ErrorResponse, HealthStatus, SystemMetrics
from ..services.health_service import HealthService

logger = logging.getLogger(__name__)


def create_health_router(health_service: HealthService) -> APIRouter:
    """Create and configure health check API router"""
    router = APIRouter(
        prefix="/health",
        tags=["health"],
        responses={
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
    )

    @router.get(  # type: ignore[misc]
        "",
        response_model=HealthStatus,
        status_code=status.HTTP_200_OK,
        summary="Health check",
        description="Basic health check endpoint for service monitoring",
    )
    async def health_check() -> HealthStatus:
        """
        Basic health check endpoint

        Returns the current health status of the MeetingMuse server.

        A successful response indicates the server is operational and
        ready to handle requests.
        """
        try:
            health_status = health_service.get_health_status()
            return HealthStatus(
                status=health_status.get("status", "unknown"),
                timestamp=datetime.now(),
                version=health_status.get("version", "unknown"),
                uptime_seconds=health_status.get("uptime_seconds", 0.0),
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Health check failed",
            )

    @router.get(  # type: ignore[misc]
        "/metrics",
        response_model=SystemMetrics,
        status_code=status.HTTP_200_OK,
        summary="System metrics",
        description="Comprehensive system metrics for monitoring and observability",
    )
    async def system_metrics() -> SystemMetrics:
        """
        Comprehensive system metrics

        Returns detailed system performance and health metrics including:
        - Overall health status
        - Active WebSocket connections
        - Message processing statistics
        - Resource usage (CPU, memory)
        - Service component status
        - Server uptime

        This endpoint provides detailed telemetry data for monitoring,
        alerting, and performance analysis.
        """
        try:
            metrics = health_service.get_system_metrics()
            return SystemMetrics(
                health_status=metrics.get("health_status", "unknown"),
                active_connections=metrics.get("active_connections", 0),
                total_messages_processed=metrics.get("total_messages_processed", 0),
                memory_usage=metrics.get("memory_usage", {}),
                cpu_usage=metrics.get("cpu_usage", 0.0),
                uptime_seconds=metrics.get("uptime_seconds", 0.0),
                langgraph_status=metrics.get("langgraph_status", "unknown"),
                streaming_handler_status=metrics.get(
                    "streaming_handler_status", "unknown"
                ),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve system metrics",
            )

    return router

"""
Health API
HTTP endpoints for system health checks and monitoring
"""
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..services.health_service import HealthService

logger = logging.getLogger(__name__)


def create_health_router(health_service: HealthService) -> APIRouter:
    """Create and configure health check API router"""
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("")  # type: ignore
    async def health_check() -> JSONResponse:
        """Basic health check endpoint"""
        health_status = health_service.get_health_status()
        return JSONResponse(health_status)

    @router.get("/metrics")  # type: ignore
    async def system_metrics() -> JSONResponse:
        """Comprehensive system metrics"""
        metrics = health_service.get_system_metrics()
        return JSONResponse(metrics)

    return router

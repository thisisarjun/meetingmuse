from fastapi import APIRouter, HTTPException, status

from common.logger import Logger
from server.models.api_dtos import ErrorResponse, HealthStatus
from server.services.health_service import HealthService


def create_health_router(
    health_service: HealthService,
    logger: Logger,
) -> APIRouter:
    """Create and configure health check API router"""
    router = APIRouter(
        prefix="/health",
        tags=["health"],
        responses={
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
    )

    @router.get(
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
            return health_status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Health check failed",
            )

    return router

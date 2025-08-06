"""
Admin API
HTTP endpoints for administrative operations and management
"""
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..services.admin_service import AdminService

logger = logging.getLogger(__name__)


def create_admin_router(admin_service: AdminService) -> APIRouter:
    """Create and configure admin API router"""
    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.post("/broadcast")  # type: ignore
    async def broadcast_message(message: Dict[str, str]) -> JSONResponse:
        """
        Broadcast a message to all connected clients

        Args:
            message: Dictionary containing message content
        """
        if "content" not in message:
            raise HTTPException(status_code=400, detail="Message content is required")

        result = await admin_service.broadcast_message(message["content"])
        return JSONResponse(result)

    @router.get("/connections")  # type: ignore
    async def get_connections() -> JSONResponse:
        """Get information about active connections"""
        connections_info = admin_service.get_connections_info()
        return JSONResponse(connections_info)

    @router.get("/statistics")  # type: ignore
    async def get_system_statistics() -> JSONResponse:
        """Get comprehensive system statistics for admin dashboard"""
        stats = admin_service.get_system_statistics()
        return JSONResponse(stats)

    @router.post("/cleanup")  # type: ignore
    async def cleanup_connections() -> JSONResponse:
        """Clean up all active connections (admin operation)"""
        result = await admin_service.cleanup_connections()
        return JSONResponse(result)

    return router

"""Tests for health API endpoints."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException


class TestHealthAPI:
    """Test suite for health API endpoints."""

    @pytest.fixture
    def mock_health_service(self):
        """Mock health service."""
        # Import the module to use in spec
        import importlib

        health_service_module = importlib.import_module(
            "server.services.health_service"
        )
        service = Mock(spec=health_service_module.HealthService)
        service.get_health_status = Mock()
        return service

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        # Import the module to use in spec
        import importlib

        logger_module = importlib.import_module("common.logger.logger")
        return Mock(spec=logger_module.Logger)

    @pytest.fixture
    def health_router(self, mock_health_service, mock_logger):
        """Create health router with mocked dependencies."""
        # Import the module dynamically
        import importlib

        health_api_module = importlib.import_module("server.api.health_api")
        return health_api_module.create_health_router(mock_health_service, mock_logger)

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_health_service, mock_logger, health_router
    ):
        """Test successful health check."""
        # Import HealthStatus dynamically
        import importlib

        health_models = importlib.import_module("server.models.api.health")

        # Arrange
        expected_health = health_models.HealthStatus(
            status="healthy", active_connections=5
        )
        mock_health_service.get_health_status.return_value = expected_health

        # Get the health check function from the router
        health_check_func = None
        for route in health_router.routes:
            if hasattr(route, "endpoint") and route.path == "/health":
                health_check_func = route.endpoint
                break

        assert health_check_func is not None, "Health check endpoint not found"

        # Act
        result = await health_check_func()

        # Assert
        assert isinstance(result, health_models.HealthStatus)
        assert result.status == "healthy"
        assert result.active_connections == 5
        mock_health_service.get_health_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_service_failure(
        self, mock_health_service, mock_logger, health_router
    ):
        """Test health check when service throws exception."""
        # Arrange
        mock_health_service.get_health_status.side_effect = Exception(
            "Service unavailable"
        )

        # Get the health check function from the router
        health_check_func = None
        for route in health_router.routes:
            if hasattr(route, "endpoint") and route.path == "/health":
                health_check_func = route.endpoint
                break

        assert health_check_func is not None, "Health check endpoint not found"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await health_check_func()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Health check failed"
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_router_configuration(self, mock_health_service, mock_logger):
        """Test that health router is properly configured."""
        # Act
        router = create_health_router(mock_health_service, mock_logger)

        # Assert
        assert router.prefix == "/health"
        assert "health" in router.tags
        assert len(router.routes) == 1  # Should have one health endpoint

        # Check the route is properly configured
        route = router.routes[0]
        assert route.path == "/health"
        assert "GET" in route.methods

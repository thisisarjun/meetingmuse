"""Tests for WebSocket API endpoints."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket, WebSocketException, status

from common.logger.logger import Logger
from server.api.websocket_api import create_websocket_router
from server.services.oauth_service import OAuthService
from server.services.websocket_connection_service import WebSocketConnectionService


class TestWebSocketAPI:
    """Test suite for WebSocket API endpoints."""

    @pytest.fixture
    def mock_oauth_service(self):
        """Mock OAuth service."""
        service = Mock(spec=OAuthService)
        service.validate_token = AsyncMock()
        return service

    @pytest.fixture
    def mock_websocket_service(self):
        """Mock WebSocket connection service."""
        service = Mock(spec=WebSocketConnectionService)
        service.handle_websocket_connection = AsyncMock()
        return service

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        return Mock(spec=Logger)

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.close = AsyncMock()
        return websocket

    @pytest.fixture
    def websocket_router(self, mock_websocket_service, mock_logger):
        """Create WebSocket router with mocked dependencies."""
        return create_websocket_router(mock_websocket_service, mock_logger)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_success(
        self,
        mock_websocket_service,
        mock_logger,
        mock_websocket,
        mock_oauth_service,
        websocket_router,
    ):
        """Test successful WebSocket connection with valid authentication."""
        # Arrange
        client_id = "test_client_123"
        session_id = "test_session_456"
        mock_oauth_service.validate_token.return_value = True

        # Get the WebSocket endpoint function from the router
        websocket_endpoint_func = None
        for route in websocket_router.routes:
            if hasattr(route, "endpoint") and route.path == "/ws/{client_id}":
                websocket_endpoint_func = route.endpoint
                break

        assert websocket_endpoint_func is not None, "WebSocket endpoint not found"

        # Act - Call the websocket endpoint with dependency injection
        await websocket_endpoint_func(
            websocket=mock_websocket,
            client_id=client_id,
            session_id=session_id,
            oauth_service=mock_oauth_service,
        )

        # Assert
        mock_oauth_service.validate_token.assert_called_once_with(session_id)
        mock_websocket_service.handle_websocket_connection.assert_called_once_with(
            mock_websocket, client_id, session_id
        )

    @pytest.mark.asyncio
    async def test_websocket_endpoint_missing_session_id(
        self,
        mock_websocket_service,
        mock_logger,
        mock_websocket,
        mock_oauth_service,
        websocket_router,
    ):
        """Test WebSocket connection with missing session_id."""
        # Arrange
        client_id = "test_client_123"
        session_id = ""  # Empty session_id

        # Get the WebSocket endpoint function from the router
        websocket_endpoint_func = None
        for route in websocket_router.routes:
            if hasattr(route, "endpoint") and route.path == "/ws/{client_id}":
                websocket_endpoint_func = route.endpoint
                break

        assert websocket_endpoint_func is not None, "WebSocket endpoint not found"

        # Act & Assert
        with pytest.raises(WebSocketException) as exc_info:
            await websocket_endpoint_func(
                websocket=mock_websocket,
                client_id=client_id,
                session_id=session_id,
                oauth_service=mock_oauth_service,
            )

        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
        assert exc_info.value.reason == "Missing session_id"
        mock_websocket.close.assert_called_once_with(
            code=status.WS_1008_POLICY_VIOLATION
        )

    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_session(
        self,
        mock_websocket_service,
        mock_logger,
        mock_websocket,
        mock_oauth_service,
        websocket_router,
    ):
        """Test WebSocket connection with invalid/expired session."""
        # Arrange
        client_id = "test_client_123"
        session_id = "invalid_session"
        mock_oauth_service.validate_token.return_value = False

        # Get the WebSocket endpoint function from the router
        websocket_endpoint_func = None
        for route in websocket_router.routes:
            if hasattr(route, "endpoint") and route.path == "/ws/{client_id}":
                websocket_endpoint_func = route.endpoint
                break

        assert websocket_endpoint_func is not None, "WebSocket endpoint not found"

        # Act & Assert
        with pytest.raises(WebSocketException) as exc_info:
            await websocket_endpoint_func(
                websocket=mock_websocket,
                client_id=client_id,
                session_id=session_id,
                oauth_service=mock_oauth_service,
            )

        assert exc_info.value.code == status.WS_1003_UNSUPPORTED_DATA
        assert exc_info.value.reason == "Invalid or expired session"
        mock_oauth_service.validate_token.assert_called_once_with(session_id)
        mock_websocket.close.assert_called_once_with(
            code=status.WS_1003_UNSUPPORTED_DATA
        )

    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_client_id(
        self,
        mock_websocket_service,
        mock_logger,
        mock_websocket,
        mock_oauth_service,
        websocket_router,
    ):
        """Test WebSocket connection with invalid client_id."""
        # Arrange
        client_id = ""  # Empty client_id
        session_id = "test_session_456"
        mock_oauth_service.validate_token.return_value = True

        # Get the WebSocket endpoint function from the router
        websocket_endpoint_func = None
        for route in websocket_router.routes:
            if hasattr(route, "endpoint") and route.path == "/ws/{client_id}":
                websocket_endpoint_func = route.endpoint
                break

        assert websocket_endpoint_func is not None, "WebSocket endpoint not found"

        # Act & Assert
        with pytest.raises(WebSocketException) as exc_info:
            await websocket_endpoint_func(
                websocket=mock_websocket,
                client_id=client_id,
                session_id=session_id,
                oauth_service=mock_oauth_service,
            )

        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
        assert exc_info.value.reason == "Invalid client_id"
        mock_websocket.close.assert_called_once_with(
            code=status.WS_1008_POLICY_VIOLATION
        )

    @pytest.mark.asyncio
    async def test_websocket_router_configuration(
        self, mock_websocket_service, mock_logger
    ):
        """Test that WebSocket router is properly configured."""
        # Act
        router = create_websocket_router(mock_websocket_service, mock_logger)

        # Assert
        assert "websocket" in router.tags
        assert len(router.routes) == 1  # Should have one WebSocket endpoint

        # Check the route is properly configured
        route = router.routes[0]
        assert route.path == "/ws/{client_id}"

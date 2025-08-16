from server.models.api_dtos import HealthStatus
from server.services.connection_manager import ConnectionManager


class HealthService:
    def __init__(
        self,
        connection_manager: ConnectionManager,
    ) -> None:
        self.connection_manager = connection_manager

    def get_health_status(self) -> HealthStatus:
        return HealthStatus(
            status="healthy",
            active_connections=self.connection_manager.get_active_connections(),
        )

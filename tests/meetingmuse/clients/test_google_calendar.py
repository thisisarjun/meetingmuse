from unittest.mock import AsyncMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from common.logger import Logger
from meetingmuse.clients.google_calendar import GoogleCalendarClient
from meetingmuse.models.meeting import CalendarEventDetails
from server.services.oauth_service import OAuthService


class TestGoogleCalendarClient:
    """Test suite for GoogleCalendarClient."""

    @pytest.fixture
    def mock_oauth_service(self):
        """Create a mock OAuth service for testing."""
        return Mock(spec=OAuthService)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def client(self, mock_oauth_service: OAuthService, mock_logger: Logger):
        """Create a GoogleCalendarClient instance with mocked dependencies."""
        return GoogleCalendarClient(mock_oauth_service, mock_logger)

    async def test_create_calendar_event_success(
        self, client: GoogleCalendarClient, mock_oauth_service: OAuthService
    ):
        """Test successful calendar event creation."""
        # Arrange
        session_id = "test-session-123"
        title = "Team Standup"
        date_time = "2025-08-25 14:30"
        duration_minutes = 30
        location = "Conference Room A"
        participants = ["test@example.com"]

        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        mock_created_event = {
            "id": "event-123",
            "htmlLink": "https://calendar.google.com/event?eid=event-123",
        }

        with patch("meetingmuse.clients.google_calendar.build") as mock_build:
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()

            mock_build.return_value = mock_service
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_insert.execute.return_value = mock_created_event

            # Act
            result = await client.create_calendar_event(
                session_id=session_id,
                title=title,
                date_time=date_time,
                duration_minutes=duration_minutes,
                location=location,
                participants=participants,
            )

            # Assert
            assert isinstance(result, CalendarEventDetails)
            assert result.event_id == "event-123"
            assert (
                result.event_link == "https://calendar.google.com/event?eid=event-123"
            )
            mock_oauth_service.get_credentials.assert_called_once_with(session_id)

    async def test_create_calendar_event_oauth_error(
        self, client: GoogleCalendarClient, mock_oauth_service: OAuthService
    ):
        """Test create_calendar_event raises ValueError when credentials are not available."""
        # Arrange
        mock_oauth_service.get_credentials = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Could not obtain valid OAuth credentials"
        ):
            await client.create_calendar_event(
                session_id="test-session",
                title="Test Meeting",
                date_time="2025-08-25 14:30",
                duration_minutes=30,
            )

    async def test_create_calendar_event_general_error(
        self,
        client: GoogleCalendarClient,
        mock_oauth_service: OAuthService,
        mock_logger: Logger,
    ):
        """Test create_calendar_event handles Google Calendar API errors."""
        # Arrange
        session_id = "test-session-123"
        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        http_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"message": "Insufficient permissions"}}',
        )

        with patch("meetingmuse.clients.google_calendar.build") as mock_build:
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()

            mock_build.return_value = mock_service
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_insert.execute.side_effect = http_error

            # Act & Assert
            with pytest.raises(ValueError, match="Failed to create calendar event"):
                await client.create_calendar_event(
                    session_id=session_id,
                    title="Test Meeting",
                    date_time="2025-08-25 14:30",
                    duration_minutes=30,
                )

            mock_logger.error.assert_called_once()

    async def test_create_calendar_event_session_id_error(
        self, client: GoogleCalendarClient
    ):
        """Test create_calendar_event raises ValueError when session_id is missing."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="No session ID available for calendar access"
        ):
            await client.create_calendar_event(
                session_id="",
                title="Test Meeting",
                date_time="2025-08-25 14:30",
                duration_minutes=30,
            )

    def test_prepare_attendees_with_participants(self, client: GoogleCalendarClient):
        """Test _prepare_attendees with valid participant list."""
        # Arrange
        participants = ["alice@example.com", "bob@example.com", "charlie@example.com"]

        # Act
        result = client._prepare_attendees(participants)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == {"email": "alice@example.com"}
        assert result[1] == {"email": "bob@example.com"}
        assert result[2] == {"email": "charlie@example.com"}

    def test_prepare_attendees_with_empty_list(self, client: GoogleCalendarClient):
        """Test _prepare_attendees with empty participant list."""
        # Arrange
        participants = []

        # Act
        result = client._prepare_attendees(participants)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_prepare_attendees_with_none(self, client: GoogleCalendarClient):
        """Test _prepare_attendees with None participants."""
        # Arrange
        participants = None

        # Act
        result = client._prepare_attendees(participants)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_prepare_attendees_with_single_participant(
        self, client: GoogleCalendarClient
    ):
        """Test _prepare_attendees with single participant."""
        # Arrange
        participants = ["single@example.com"]

        # Act
        result = client._prepare_attendees(participants)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == {"email": "single@example.com"}

    async def test_create_calendar_event_with_multiple_participants(
        self, client: GoogleCalendarClient, mock_oauth_service: OAuthService
    ):
        """Test successful calendar event creation with multiple participants."""
        # Arrange
        session_id = "test-session-123"
        title = "Team Planning Meeting"
        date_time = "2025-08-25 14:30"
        duration_minutes = 60
        location = "Conference Room B"
        participants = ["alice@example.com", "bob@example.com", "charlie@example.com"]

        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        mock_created_event = {
            "id": "event-456",
            "htmlLink": "https://calendar.google.com/event?eid=event-456",
        }

        with patch("meetingmuse.clients.google_calendar.build") as mock_build:
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()

            mock_build.return_value = mock_service
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_insert.execute.return_value = mock_created_event

            # Act
            result = await client.create_calendar_event(
                session_id=session_id,
                title=title,
                date_time=date_time,
                duration_minutes=duration_minutes,
                location=location,
                participants=participants,
            )

            # Assert
            assert isinstance(result, CalendarEventDetails)
            assert result.event_id == "event-456"
            assert (
                result.event_link == "https://calendar.google.com/event?eid=event-456"
            )

            # Verify the event payload included all participants
            call_args = mock_events.insert.call_args
            event_payload = call_args.kwargs["body"]
            assert len(event_payload["attendees"]) == 3
            assert {"email": "alice@example.com"} in event_payload["attendees"]
            assert {"email": "bob@example.com"} in event_payload["attendees"]
            assert {"email": "charlie@example.com"} in event_payload["attendees"]

    async def test_create_calendar_event_without_participants(
        self, client: GoogleCalendarClient, mock_oauth_service: OAuthService
    ):
        """Test successful calendar event creation without participants."""
        # Arrange
        session_id = "test-session-123"
        title = "Personal Task"
        date_time = "2025-08-25 14:30"
        duration_minutes = 30

        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        mock_created_event = {
            "id": "event-789",
            "htmlLink": "https://calendar.google.com/event?eid=event-789",
        }

        with patch("meetingmuse.clients.google_calendar.build") as mock_build:
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()

            mock_build.return_value = mock_service
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_insert.execute.return_value = mock_created_event

            # Act
            result = await client.create_calendar_event(
                session_id=session_id,
                title=title,
                date_time=date_time,
                duration_minutes=duration_minutes,
                participants=None,
            )

            # Assert
            assert isinstance(result, CalendarEventDetails)
            assert result.event_id == "event-789"

            # Verify the event payload has no attendees
            call_args = mock_events.insert.call_args
            event_payload = call_args.kwargs["body"]
            assert len(event_payload["attendees"]) == 0

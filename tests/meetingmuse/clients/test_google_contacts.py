from unittest.mock import AsyncMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from common.logger import Logger
from meetingmuse.clients.google_contacts import GoogleContactsClient
from server.services.oauth_service import OAuthService


class TestGoogleContactsClient:
    """Test suite for GoogleContactsClient."""

    @pytest.fixture
    def mock_oauth_service(self):
        """Create a mock OAuth service for testing."""
        return Mock(spec=OAuthService)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def client(
        self, mock_oauth_service: OAuthService, mock_logger: Logger
    ) -> GoogleContactsClient:
        """Create a GoogleContactsClient instance with mocked dependencies."""
        return GoogleContactsClient(mock_oauth_service, mock_logger)

    @pytest.fixture
    def sample_people_response(self):
        """Sample response from Google People API with mixed contacts."""
        return {
            "results": [
                {
                    "person": {
                        "etag": "%EgUBCS43PhoBAiIMRGtkYlBVeWhRckE9",
                        "resourceName": "people/c4383599497656573845",
                    }
                },
                {
                    "person": {
                        "etag": "%EgUBCS43PhoBAiIMSE5SNlJXT0dOZXM9",
                        "resourceName": "people/c805666995185635310",
                    }
                },
                {
                    "person": {
                        "emailAddresses": [
                            {
                                "formattedType": "Other",
                                "metadata": {
                                    "primary": True,
                                    "verified": True,
                                    "source": {"type": "CONTACT", "id": "12345"},
                                    "sourcePrimary": True,
                                },
                                "type": "Other",
                                "value": "user1@example.com",
                            }
                        ],
                        "etag": "%EgUBCS43PhoBAiIMVXliS0NaaERpNTg9",
                        "resourceName": "people/c6834058438680022123",
                    }
                },
                {
                    "person": {
                        "emailAddresses": [
                            {
                                "formattedType": "Work",
                                "metadata": {"primary": False, "verified": True},
                                "type": "Work",
                                "value": "user2@work.com",
                            }
                        ],
                        "etag": "%EgUBCS43PhoBAiIMREhZZk56QW1xa1E9",
                        "resourceName": "people/c8461244257298983167",
                    }
                },
                {
                    "person": {
                        "etag": "%EgUBCS43PhoBAiIMTVZDOXFld2FyZVk9",
                        "resourceName": "people/c5908327675302581267",
                    }
                },
            ]
        }

    @pytest.fixture
    def empty_people_response(self):
        """Empty response from Google People API."""
        return {"results": []}

    async def test_get_contacts_success_with_emails(
        self, client, mock_oauth_service, sample_people_response
    ):
        """Test successful contact retrieval filtering contacts with emails."""
        # Arrange
        session_id = "test-session-123"
        query = "test"

        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        with patch("meetingmuse.clients.google_contacts.build") as mock_build:
            mock_service = Mock()
            mock_people = Mock()
            mock_search = Mock()

            mock_build.return_value = mock_service
            mock_service.people.return_value = mock_people
            mock_people.searchContacts.return_value = mock_search
            mock_search.execute.return_value = sample_people_response

            # Act
            result = await client.get_contacts(query=query, session_id=session_id)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 2  # Only contacts with email addresses
            assert "user1@example.com" in result
            assert "user2@work.com" in result

            # Verify API call parameters
            mock_people.searchContacts.assert_called_once_with(
                query=query,
                readMask="emailAddresses",
                pageSize=10,
            )
            mock_oauth_service.get_credentials.assert_called_once_with(session_id)

    async def test_get_contacts_empty_response(
        self, client, mock_oauth_service, empty_people_response
    ):
        """Test contact retrieval with empty response."""
        # Arrange
        session_id = "test-session-123"
        query = "nonexistent"

        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        with patch("meetingmuse.clients.google_contacts.build") as mock_build:
            mock_service = Mock()
            mock_people = Mock()
            mock_search = Mock()

            mock_build.return_value = mock_service
            mock_service.people.return_value = mock_people
            mock_people.searchContacts.return_value = mock_search
            mock_search.execute.return_value = empty_people_response

            # Act
            result = await client.get_contacts(query=query, session_id=session_id)

            # Assert
            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_contacts_no_session_id(self, client: GoogleContactsClient):
        """Test get_contacts raises ValueError when session_id is missing."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="No session ID available for calendar access"
        ):
            await client.get_contacts(query="test", session_id="")

    async def test_get_contacts_oauth_error(
        self, client: GoogleContactsClient, mock_oauth_service: OAuthService
    ):
        """Test get_contacts raises ValueError when credentials are not available."""
        # Arrange
        mock_oauth_service.get_credentials = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Could not obtain valid OAuth credentials"
        ):
            await client.get_contacts(query="test", session_id="test-session")

    async def test_get_contacts_http_error(
        self,
        client: GoogleContactsClient,
        mock_oauth_service: OAuthService,
        mock_logger: Logger,
    ):
        """Test get_contacts handles Google People API errors."""
        # Arrange
        session_id = "test-session-123"
        mock_oauth_service.get_credentials = AsyncMock(return_value=Mock())

        http_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"message": "Insufficient permissions"}}',
        )

        with patch("meetingmuse.clients.google_contacts.build") as mock_build:
            mock_service = Mock()
            mock_people = Mock()
            mock_search = Mock()

            mock_build.return_value = mock_service
            mock_service.people.return_value = mock_people
            mock_people.searchContacts.return_value = mock_search
            mock_search.execute.side_effect = http_error

            # Act & Assert
            with pytest.raises(ValueError, match="Failed to get contacts"):
                await client.get_contacts(query="test", session_id=session_id)

            mock_logger.error.assert_called_once()

    def test_extract_email_addresses_success(
        self, client: GoogleContactsClient, sample_people_response
    ):
        """Test _extract_email_addresses method with valid response."""
        # Act
        result = client._extract_email_addresses(sample_people_response)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert "user1@example.com" in result
        assert "user2@work.com" in result

    def test_extract_email_addresses_empty_response(self, client: GoogleContactsClient):
        """Test _extract_email_addresses with empty response."""
        # Arrange
        empty_response = {"results": []}

        # Act
        result = client._extract_email_addresses(empty_response)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_email_addresses_no_emails(self, client: GoogleContactsClient):
        """Test _extract_email_addresses with contacts having no emails."""
        # Arrange
        response_no_emails = {
            "results": [
                {
                    "person": {
                        "etag": "%EgUBCS43PhoBAiIMRGtkYlBVeWhRckE9",
                        "resourceName": "people/c4383599497656573845",
                    }
                },
                {
                    "person": {
                        "etag": "%EgUBCS43PhoBAiIMSE5SNlJXT0dOZXM9",
                        "resourceName": "people/c805666995185635310",
                    }
                },
            ]
        }

        # Act
        result = client._extract_email_addresses(response_no_emails)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

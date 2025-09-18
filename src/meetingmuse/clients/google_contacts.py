from typing import List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from common.logger.logger import Logger
from meetingmuse.models.google_apis import PeopleSearchResponse
from server.services.oauth_service import OAuthService


class GoogleContactsClient:
    def __init__(self, oauth_service: OAuthService, logger: Logger):
        self.oauth_service = oauth_service
        self.logger = logger

    def _extract_email_addresses(self, people_list: dict) -> List[str]:
        """
        Extract email addresses from Google People API response.

        Args:
            people_list: Raw response from Google People API searchContacts

        Returns:
            List of email addresses from contacts that have emails
        """
        # Validate and parse the response using Pydantic model
        people_response = PeopleSearchResponse(**people_list)

        email_addresses = []

        for result in people_response.results:
            person = result.person

            # Only include contacts that have email addresses
            if person.emailAddresses:
                # Get the primary email address (first one in the list)
                primary_email = person.emailAddresses[0].value
                if primary_email:
                    email_addresses.append(primary_email)

        return email_addresses

    async def get_contacts(self, query: str, session_id: str) -> List[str]:
        if not session_id:
            raise ValueError("No session ID available for calendar access")

        # Get OAuth credentials
        credentials = await self.oauth_service.get_credentials(session_id)
        if not credentials:
            raise ValueError("Could not obtain valid OAuth credentials")

        service = build("people", "v1", credentials=credentials)

        try:
            people_list = (
                service.people()
                .searchContacts(
                    query=query,
                    readMask="emailAddresses",
                    pageSize=10,
                )
                .execute()
            )
            return self._extract_email_addresses(people_list)

        except HttpError as e:
            self.logger.error(f"Google Contacts API error: {str(e)}")
            raise ValueError(f"Failed to get contacts: {str(e)}") from e

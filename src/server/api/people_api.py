"""People API for contact search functionality."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from common.logger.logger import Logger
from meetingmuse.clients.google_contacts import GoogleContactsClient

from .dependencies import get_google_contacts_client, get_logger


async def search_contacts(
    query: str = Query(..., description="Search query for contacts", min_length=1),
    session_id: str = Query(..., description="Session ID for authentication"),
    contacts_client: GoogleContactsClient = Depends(get_google_contacts_client),
    logger: Logger = Depends(get_logger),
) -> List[str]:
    """
    Search for contacts by name or email.

    This endpoint searches through the user's Google contacts and returns
    a list of email addresses that match the search query.

    Args:
        query: Search string to find contacts
        session_id: User session ID for OAuth authentication
        contacts_client: Injected Google Contacts client
        logger: Injected logger service

    Returns:
        List of email addresses matching the search query

    Raises:
        HTTPException: If authentication fails or API error occurs
    """
    try:
        logger.info("starting_contacts_search")

        # Call the Google Contacts API to search for contacts
        email_addresses = await contacts_client.get_contacts(
            query=query, session_id=session_id
        )

        logger.info("success_contacts_search")
        return email_addresses

    except ValueError as e:
        # Handle authentication and API errors
        error_msg = str(e)
        logger.error(f"Contact search failed for session {session_id}: {error_msg}")

        if "OAuth credentials" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please sign in with Google.",
            )
        elif "session ID" in error_msg:
            raise HTTPException(status_code=400, detail="Invalid session ID provided.")
        else:
            raise HTTPException(
                status_code=503,
                detail="Google Contacts service temporarily unavailable.",
            )
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error during contact search for session {session_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while searching contacts.",
        )


def create_people_router() -> APIRouter:
    """Create and configure People API router."""
    router: APIRouter = APIRouter(prefix="/people", tags=["people"])

    # Add routes with proper typing
    router.add_api_route(
        "/contacts/search",
        search_contacts,
        methods=["GET"],
        response_model=List[str],
    )

    return router

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EmailAddressMetadata(BaseModel):
    """Metadata for an email address from Google People API."""

    primary: Optional[bool] = None
    verified: Optional[bool] = None
    source: Optional[Dict[str, Any]] = None
    sourcePrimary: Optional[bool] = None


class EmailAddress(BaseModel):
    """Email address structure from Google People API."""

    metadata: Optional[EmailAddressMetadata] = None
    value: str
    type: Optional[str] = None
    formattedType: Optional[str] = None


class Person(BaseModel):
    """Person structure from Google People API."""

    resourceName: str
    etag: str
    emailAddresses: Optional[List[EmailAddress]] = None
    names: Optional[List[Dict[str, Any]]] = None
    phoneNumbers: Optional[List[Dict[str, Any]]] = None
    addresses: Optional[List[Dict[str, Any]]] = None
    organizations: Optional[List[Dict[str, Any]]] = None


class PersonResult(BaseModel):
    """Individual result from Google People API search."""

    person: Person


class PeopleSearchResponse(BaseModel):
    """Complete response from Google People API searchContacts method."""

    results: List[PersonResult] = []
    nextPageToken: Optional[str] = None
    totalSize: Optional[int] = None


class ContactEmail(BaseModel):
    """Simplified contact email model for internal use."""

    email: str
    name: Optional[str] = None
    resource_name: Optional[str] = None

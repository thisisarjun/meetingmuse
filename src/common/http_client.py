"""Common HTTP client for async requests."""

from typing import Any, Optional

import httpx


class HttpClient:
    """Async HTTP client for making requests."""

    def __init__(
        self,
        base_url: str = "",
        headers: Optional[dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize HTTP client.

        Args:
            base_url: Base URL for requests
            headers: Default headers to include
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.default_headers = headers or {}
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=base_url, headers=self.default_headers, timeout=timeout
        )

    async def __aenter__(self) -> "HttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def post(
        self,
        url: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make POST request.

        Args:
            url: Request URL
            json: JSON payload
            data: Form data payload
            params: Query parameters
            headers: Additional headers

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If request fails
        """
        merged_headers = {**self.default_headers, **(headers or {})}
        response = await self.client.post(
            url, json=json, data=data, params=params, headers=merged_headers
        )
        response.raise_for_status()
        return response


http_client = HttpClient()

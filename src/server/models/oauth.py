from pydantic import BaseModel


class WebClientConfig(BaseModel):
    """Web client configuration for OAuth."""

    client_id: str
    client_secret: str
    redirect_uris: list[str]
    auth_uri: str
    token_uri: str


class ClientConfig(BaseModel):
    """OAuth client configuration."""

    web: WebClientConfig

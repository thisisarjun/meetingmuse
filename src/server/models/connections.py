from pydantic import BaseModel


class ConnectionMetadataDto(BaseModel):
    connected_at: str
    message_count: int

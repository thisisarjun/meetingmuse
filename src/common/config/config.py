import os
from typing import List

from dotenv import load_dotenv
from pydantic import SecretStr

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for MeetingMuse."""

    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN", "")
    ENV: str = os.getenv("ENV", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    OPENAI_API_KEY = SecretStr(os.getenv("OPENAI_API_KEY", ""))
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "123")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "123")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback"
    )
    FRONTEND_CALLBACK_URL: str = os.getenv(
        "FRONTEND_CALLBACK_URL", "http://localhost:3000/"
    )
    GOOGLE_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/contacts.readonly",
    ]

    # Security Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    SESSION_ENCRYPTION_KEY: str = os.getenv("SESSION_ENCRYPTION_KEY", "")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    @classmethod
    def validate(cls) -> None:
        """Validate that all required environment variables are set."""
        if not cls.HUGGINGFACE_API_TOKEN or cls.HUGGINGFACE_API_TOKEN.strip() == "":
            raise ValueError("HUGGINGFACE_API_TOKEN is required but not set")
        if not cls.GOOGLE_CLIENT_ID or cls.GOOGLE_CLIENT_ID.strip() == "":
            raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
        if not cls.GOOGLE_CLIENT_SECRET or cls.GOOGLE_CLIENT_SECRET.strip() == "":
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")
        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY.strip() == "":
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        if not cls.SESSION_ENCRYPTION_KEY or cls.SESSION_ENCRYPTION_KEY.strip() == "":
            raise ValueError("SESSION_ENCRYPTION_KEY environment variable is required")


# Create a singleton instance
config: Config = Config()

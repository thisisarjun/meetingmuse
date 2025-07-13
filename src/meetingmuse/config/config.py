import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for MeetingMuse."""
    
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        if not cls.HUGGINGFACE_API_TOKEN:
            raise ValueError("HUGGINGFACE_API_TOKEN is required but not set")

# Create a singleton instance
config = Config() 
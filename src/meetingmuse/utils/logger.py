"""Simple console logger utility for MeetingMuse."""

import logging
import sys


class Logger:
    """Simple console logger class."""
    
    def __init__(self):
        """Initialize the logger."""
        self.logger = logging.getLogger("meetingmuse")
        
        # Avoid adding handlers multiple times
        if not self.logger.handlers:
            # Create console handler
            handler = logging.StreamHandler(sys.stdout)
            
            # Create formatter
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

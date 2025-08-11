"""Simple console logger utility for MeetingMuse with color support."""

import logging
import sys
from typing import TextIO, Union


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }

    RESET = "\033[0m"  # Reset color
    BOLD = "\033[1m"  # Bold text

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Get the color for this log level
        color: str = self.COLORS.get(record.levelname, "")

        # Create the base format
        log_format: str = f"{self.BOLD}%(asctime)s{self.RESET} - {color}{self.BOLD}%(levelname)s{self.RESET} - {color}%(message)s{self.RESET}"  # pylint: disable=line-too-long

        # Create formatter with the colored format
        formatter: logging.Formatter = logging.Formatter(
            fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S"
        )

        return formatter.format(record)


class Logger:
    """Simple console logger class with color support and optional prefix."""

    logger: logging.Logger
    enable_colors: bool
    prefix: str

    def __init__(self, enable_colors: bool = True) -> None:
        """Initialize the logger.

        Args:
            enable_colors: Whether to enable colored output (default: True)
            prefix: Optional prefix to add to all log messages (e.g., "NodeName")
        """
        self.logger = logging.getLogger("meetingmuse")
        self.enable_colors = enable_colors
        self.prefix = ""

        # Avoid adding handlers multiple times
        if not self.logger.handlers:
            # Create console handler
            handler: logging.StreamHandler[TextIO] = logging.StreamHandler(sys.stdout)

            # Create formatter (colored or plain)
            formatter: Union[ColoredFormatter, logging.Formatter]
            if self.enable_colors and self._supports_color():
                formatter = ColoredFormatter()
            else:
                formatter = logging.Formatter(
                    fmt="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        # Check if stdout is a TTY and supports colors
        return (
            hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
            and sys.platform != "win32"  # Simple check for non-Windows
        )

    def _add_prefix(self, message: str) -> str:
        """Add prefix to message if one is set."""
        if self.prefix and not message.startswith(self.prefix):
            return f"{self.prefix}: {message}"
        return message

    def set_prefix(self, prefix: str) -> None:
        """Set or update the prefix for this logger."""
        self.prefix = f"[{prefix}]" if prefix else ""

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(self._add_prefix(message))

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(self._add_prefix(message))

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(self._add_prefix(message))

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(self._add_prefix(message))

    def success(self, message: str) -> None:
        """Log a success message (using info level with special formatting)."""
        prefixed_message = self._add_prefix(message)
        if self.enable_colors and self._supports_color():
            # Green background with white text for success
            colored_message: str = f"\033[42m\033[30m ✓ {prefixed_message} \033[0m"
            self.logger.info(colored_message)
        else:
            self.logger.info(f"✓ {prefixed_message}")

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(self._add_prefix(message))

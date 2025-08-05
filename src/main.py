#!/usr/bin/env python3
"""
MeetingMuse CLI Entry Point
"""

from meetingmuse.utils import Logger


def main() -> None:
    """Main entry point for the MeetingMuse CLI."""
    logger: Logger = Logger()
    logger.info("Welcome to MeetingMuse - Your favourite calendar bot!")
    # TODO: Implement CLI interface


if __name__ == "__main__":
    main()

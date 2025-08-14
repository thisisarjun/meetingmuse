import functools
from typing import Any, Callable

from common.logger import Logger
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState


def log_node_entry(prefix: NodeName) -> Callable:
    """
    Decorator to automatically log when entering a node_action method.
    Adds debug logging with node name and state information.

    Args:
        prefix: prefix to add to the log message  NodeName

    Usage:
        @log_node_entry(NodeName.GREETING)  # [GREETING]
        @log_node_entry(NodeName.COLLECTING_INFO)  # [COLLECTING_INFO]
        @log_node_entry(NodeName.SCHEDULE_MEETING)  # [SCHEDULE_MEETING]
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(
            self: Any, state: MeetingMuseBotState, *args: Any, **kwargs: Any
        ) -> Any:
            # Try to get logger from the instance, fall back to creating one
            logger = getattr(self, "logger", None) or Logger()

            # Get node name for logging
            # FIXME: this is not working
            node_name = getattr(self, "node_name", self.__class__.__name__)

            # Determine prefix
            log_prefix = f"[{prefix}]"

            # Log entry with useful debug info
            logger.info(
                f"{log_prefix} Entering {node_name} | Messages: {len(state.messages)} \
                    | last Message: {state.messages[-1] if state.messages else 'None'} \
                        | State: {state.meeting_details}"
            )

            # Call the original method
            return func(self, state, *args, **kwargs)

        return wrapper

    return decorator

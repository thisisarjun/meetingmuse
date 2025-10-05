import functools
import inspect
from typing import Any, Callable

from common.logger import Logger
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState


def log_node_entry(prefix: NodeName) -> Callable:
    """
    Decorator to automatically log when entering a node_action method.
    Adds debug logging with node name and state information.
    Supports both sync and async functions.

    Args:
        prefix: prefix to add to the log message  NodeName

    Usage:
        @log_node_entry(NodeName.GREETING)  # [GREETING]
        @log_node_entry(NodeName.COLLECTING_INFO)  # [COLLECTING_INFO]
        @log_node_entry(NodeName.SCHEDULE_MEETING)  # [SCHEDULE_MEETING]
    """

    def logger_helper(self: Any, state: MeetingMuseBotState) -> None:
        """
        Helper function to get the logger from the instance.
        """
        logger = getattr(self, "logger", None) or Logger()

        node_name = getattr(self, "node_name", self.node_name)
        # Determine prefix
        log_prefix = f"[{prefix}]"

        # Log entry with useful debug info
        logger.info(
            f"{log_prefix} Entering {node_name} | Messages: {len(state.messages)} \
                | last Message: {state.messages[-1] if state.messages else 'None'} \
                    | State: {state.meeting_details}"
        )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(
            self: Any, state: MeetingMuseBotState, *args: Any, **kwargs: Any
        ) -> Any:
            # Try to get logger from the instance, fall back to creating one
            self.logger_helper(state)

            # Call the original method (await if it's async)
            return await func(self, state, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(
            self: Any, state: MeetingMuseBotState, *args: Any, **kwargs: Any
        ) -> Any:
            # Try to get logger from the instance, fall back to creating one
            logger_helper(self, state)

            # Call the original method
            return func(self, state, *args, **kwargs)

        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

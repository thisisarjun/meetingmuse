"""
Message Processor for graph Integration
Handles message processing through the graph workflow
"""

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from common.logger import Logger
from meetingmuse.graph.graph_utils import Utils
from meetingmuse.models.graph import MessageType
from meetingmuse.models.state import MeetingMuseBotState


class GraphMessageProcessor:
    """Processes user messages through graph workflow"""

    def __init__(self, graph: CompiledStateGraph, logger: Logger) -> None:
        # pass built graph to this class
        self.graph = graph
        self.logger = logger

    async def process_user_message(self, content: str, client_id: str) -> str:
        """
        Process user message through graph workflow

        Args:
            content: User message content
            client_id: Client identifier (maps to thread_id)

        Returns:
            AI response content
        """
        try:
            input_data = {"messages": [HumanMessage(content=content)]}

            config = RunnableConfig(configurable={"thread_id": client_id})

            self.logger.info(
                f"Processing message for client {client_id}: {content[:50]}..."
            )

            # Process through graph workflow
            result = await self.graph.ainvoke(input_data, config=config)

            interrupt_info = Utils.get_interrupt_info_from_events(result)
            if interrupt_info:
                return interrupt_info.question

            meeting_muse_state = MeetingMuseBotState.model_validate(result)
            last_message = Utils.get_last_message(meeting_muse_state, MessageType.AI)
            # Extract AI response
            if last_message:
                return last_message

            self.logger.warning(f"No messages in result for client {client_id}")
            return "I'm having trouble processing your request. Please try again."

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Error processing message for client {client_id}: {str(e)}"
            )
            return "I encountered an error processing your request. Please try again."

    async def check_if_interrupt_exists(self, client_id: str) -> bool:
        """
        Handle graph interrupts for user input collection

        Args:
            client_id: Client identifier (maps to thread_id)

        Returns:
            Dictionary with interrupt information or None if no interrupts
        """
        try:
            config = RunnableConfig(configurable={"thread_id": client_id})
            current_state = self.graph.get_state(config)

            if current_state and current_state.next:
                # Graph is interrupted and waiting for user input
                return True

            return False

        except Exception as e:
            self.logger.error(
                f"Error handling interrupts for client {client_id}: {str(e)}"
            )
            raise e

    async def get_conversation_state(self, client_id: str) -> bool:
        """
        Get current conversation state for a client

        Args:
            client_id: Client identifier (maps to thread_id)

        Returns:
            True if there is a conversation, False otherwise
        """
        try:
            config = RunnableConfig(configurable={"thread_id": client_id})
            current_state = self.graph.get_state(config)

            if current_state and current_state.values:
                return True

            return False

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Error getting conversation state for client {client_id}: {str(e)}"
            )
            return False

    async def resume_interrupt_conversation(
        self, client_id: str, user_input: str
    ) -> str:
        """
        Resume an interrupted conversation with user input

        Args:
            client_id: Client identifier
            user_input: User's response to the interrupt

        Returns:
            AI response after resuming
        """
        try:
            config = RunnableConfig(configurable={"thread_id": client_id})

            # Resume the conversation with user input
            result = None
            new_interrupt_detected = False

            async for event in self.graph.astream(
                Command(resume=user_input), config, stream_mode="updates"
            ):
                if "__interrupt__" in event:
                    new_interrupt_detected = True
                    self.logger.info(
                        f"New interrupt detected after resume for client {client_id}"
                    )
                result = event

            # If a new interrupt was detected, get the interrupt info from final state
            if new_interrupt_detected:
                current_state = self.graph.get_state(config)
                interrupt_info = Utils.get_interrupt_info_from_state_snapshot(
                    current_state
                )
                if interrupt_info:
                    return interrupt_info.question
                return "I need additional information to continue."

            # Extract the latest AI response
            meeting_muse_state = MeetingMuseBotState.model_validate(result)
            last_message = Utils.get_last_message(meeting_muse_state, MessageType.AI)
            if last_message:
                return last_message

            return "Thank you for the additional information. Let me continue processing your request."

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Error resuming conversation for client {client_id}: {str(e)}"
            )
            return (
                "I encountered an error while processing your input. Please try again."
            )

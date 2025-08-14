"""
Message Processor for graph Integration
Handles message processing through the graph workflow
"""
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from common.logger import Logger
from common.utils.utils import Utils
from meetingmuse.models.interrupts import InterruptInfo
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

            meeting_muse_state = MeetingMuseBotState.model_validate(result)
            last_message = Utils.get_last_message(meeting_muse_state, "ai")
            # Extract AI response
            if last_message:
                return last_message
            else:
                self.logger.warning(f"No messages in result for client {client_id}")
                return "I'm having trouble processing your request. Please try again."

        except Exception as e:
            self.logger.error(
                f"Error processing message for client {client_id}: {str(e)}"
            )
            return "I encountered an error processing your request. Please try again."

    async def check_for_interrupts(self, client_id: str) -> Optional[InterruptInfo]:
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
                interrupt_info = current_state.interrupts[0]
                assert isinstance(interrupt_info, InterruptInfo)
                return interrupt_info

            return None

        except Exception as e:
            self.logger.error(
                f"Error handling interrupts for client {client_id}: {str(e)}"
            )
            return None

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

        except Exception as e:
            self.logger.error(
                f"Error getting conversation state for client {client_id}: {str(e)}"
            )
            return False

    async def resume_conversation(self, client_id: str, user_input: str) -> str:
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
            async for chunk in self.graph.astream(
                Command(resume=user_input), config, stream_mode="values"
            ):
                result = chunk

            # Extract the latest AI response
            meeting_muse_state = MeetingMuseBotState.model_validate(result)
            last_message = Utils.get_last_message(meeting_muse_state, "ai")
            if last_message:
                return last_message

            return "Thank you for the additional information. Let me continue processing your request."

        except Exception as e:
            self.logger.error(
                f"Error resuming conversation for client {client_id}: {str(e)}"
            )
            return (
                "I encountered an error while processing your input. Please try again."
            )

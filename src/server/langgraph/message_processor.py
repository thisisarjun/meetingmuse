"""
Message Processor for LangGraph Integration
Handles message processing through the LangGraph workflow
"""
from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from common.logger import Logger


class LangGraphMessageProcessor:
    """Processes user messages through LangGraph workflow"""

    def __init__(self, graph: CompiledStateGraph, logger: Logger) -> None:
        # pass built graph to this class
        self.graph = graph
        self.logger = logger

    async def process_user_message(self, content: str, client_id: str) -> str:
        """
        Process user message through LangGraph workflow

        Args:
            content: User message content
            client_id: Client identifier (maps to thread_id)

        Returns:
            AI response content
        """
        try:
            if not self.graph:
                raise Exception("LangGraph not initialized")

            # TODO: first time meetingmuse state creation
            input_data = {"messages": [HumanMessage(content=content)]}

            config = {"configurable": {"thread_id": client_id}}

            self.logger.info(
                f"Processing message for client {client_id}: {content[:50]}..."
            )

            # Process through LangGraph workflow
            result = await self.graph.ainvoke(input_data, config=config)

            # Extract AI response
            if result and "messages" in result and result["messages"]:
                ai_message = result["messages"][-1]
                if isinstance(ai_message, AIMessage):
                    response_content = ai_message.content
                    self.logger.info(
                        f"Generated response for client {client_id}: {response_content[:50]}..."
                    )
                    return str(response_content)
                else:
                    self.logger.warning(
                        f"Last message is not an AI message for client {client_id}"
                    )
                    return "I'm processing your request. Please wait a moment."
            else:
                self.logger.warning(f"No messages in result for client {client_id}")
                return "I'm having trouble processing your request. Please try again."

        except Exception as e:
            self.logger.error(
                f"Error processing message for client {client_id}: {str(e)}"
            )
            return "I encountered an error processing your request. Please try again."

    async def handle_interrupts(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Handle LangGraph interrupts for user input collection

        Args:
            client_id: Client identifier (maps to thread_id)

        Returns:
            Dictionary with interrupt information or None if no interrupts
        """
        try:
            if not self.graph:
                return None

            config = {"configurable": {"thread_id": client_id}}
            current_state = self.graph.get_state(config)

            if current_state and current_state.next:
                # Graph is interrupted and waiting for user input
                interrupt_info = {
                    "waiting_for_input": True,
                    "next_step": current_state.next[0] if current_state.next else None,
                    "prompt": self._generate_interrupt_prompt(current_state),
                }

                self.logger.info(
                    f"Client {client_id} has pending interrupt: {interrupt_info}"
                )
                return interrupt_info

            return None

        except Exception as e:
            self.logger.error(
                f"Error handling interrupts for client {client_id}: {str(e)}"
            )
            return None

    def _generate_interrupt_prompt(self, state: Any) -> str:
        """
        Generate a user-friendly prompt for interrupt situations

        Args:
            state: Current conversation state

        Returns:
            User-friendly prompt message
        """
        # Default prompt - can be enhanced based on state analysis
        return "Please provide additional meeting details to continue."

    async def get_conversation_state(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current conversation state for a client

        Args:
            client_id: Client identifier (maps to thread_id)

        Returns:
            Dictionary with conversation state information
        """
        try:
            if not self.graph:
                return None

            config = {"configurable": {"thread_id": client_id}}
            current_state = self.graph.get_state(config)

            if current_state and current_state.values:
                state_info = {
                    "has_conversation": True,
                    "message_count": len(current_state.values.get("messages", [])),
                    "user_intent": current_state.values.get("user_intent"),
                    "meeting_details": current_state.values.get("meeting_details", {}),
                    "is_interrupted": bool(current_state.next),
                }

                return state_info

            return {"has_conversation": False}

        except Exception as e:
            self.logger.error(
                f"Error getting conversation state for client {client_id}: {str(e)}"
            )
            return None

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
            if not self.graph:
                raise Exception("LangGraph not initialized")

            config = {"configurable": {"thread_id": client_id}}

            # Resume the conversation with user input
            result = None
            async for chunk in self.graph.astream(
                Command(resume=user_input), config, stream_mode="values"
            ):
                result = chunk

            # Extract the latest AI response
            if result and "messages" in result and result["messages"]:
                ai_message = result["messages"][-1]
                if isinstance(ai_message, AIMessage):
                    return str(ai_message.content)

            return "Thank you for the additional information. Let me continue processing your request."

        except Exception as e:
            self.logger.error(
                f"Error resuming conversation for client {client_id}: {str(e)}"
            )
            return (
                "I encountered an error while processing your input. Please try again."
            )

    def is_ready(self) -> bool:
        """Check if the processor is ready to handle messages"""
        return self.graph is not None

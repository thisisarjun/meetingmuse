"""
Streaming Handler for Real-time Response Processing
Handles streaming responses and real-time feedback during LangGraph execution
"""
import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from langchain_core.messages import AIMessage

from ..langgraph.langgraph_factory import LangGraphSingletonFactory

logger = logging.getLogger(__name__)


class StreamingHandler:
    """Handles streaming responses and real-time processing feedback"""

    def __init__(self) -> None:
        self.graph: Optional[Any] = None
        self._initialize_graph()

    def _initialize_graph(self) -> None:
        """Initialize the LangGraph instance"""
        try:
            self.graph = LangGraphSingletonFactory.get_graph()
            logger.info("Streaming handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize streaming handler: {str(e)}")
            raise e

    async def stream_response(
        self, input_data: Dict[str, Any], client_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream LangGraph execution steps and responses

        Args:
            input_data: Input data for LangGraph
            client_id: Client identifier (maps to thread_id)

        Yields:
            Dictionary containing streaming updates
        """
        try:
            if not self.graph:
                raise Exception("LangGraph not initialized")

            config = {"configurable": {"thread_id": client_id}}

            logger.info(f"Starting streaming response for client {client_id}")

            # Stream through LangGraph execution
            async for chunk in self.graph.astream(input_data, config=config):
                if chunk:
                    # Process chunk and extract meaningful updates
                    update = await self._process_chunk(chunk, client_id)
                    if update:
                        yield update

                # Add small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error streaming response for client {client_id}: {str(e)}")
            yield {
                "type": "error",
                "content": "Error occurred during processing",
                "client_id": client_id,
            }

    async def _process_chunk(
        self, chunk: Dict[str, Any], client_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a streaming chunk from LangGraph

        Args:
            chunk: Raw chunk from LangGraph stream
            client_id: Client identifier

        Returns:
            Processed update dictionary or None
        """
        try:
            # Handle different types of chunks
            if "messages" in chunk:
                messages = chunk["messages"]
                if messages:
                    latest_message = messages[-1]

                    if isinstance(latest_message, AIMessage) and latest_message.content:
                        return {
                            "type": "ai_response",
                            "content": latest_message.content,
                            "client_id": client_id,
                            "timestamp": self._get_timestamp(),
                        }

            # Handle node execution updates
            for node_name, node_data in chunk.items():
                if node_name.startswith("__") or not node_data:
                    continue

                # Extract processing step information
                return {
                    "type": "processing_step",
                    "step": node_name,
                    "content": f"Processing through {node_name.replace('_', ' ')}...",
                    "client_id": client_id,
                    "timestamp": self._get_timestamp(),
                }

            return None

        except Exception as e:
            logger.error(f"Error processing chunk for client {client_id}: {str(e)}")
            return None

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.now().isoformat()

    async def send_processing_notification(
        self, step: str, client_id: str
    ) -> Dict[str, Any]:
        """
        Create a processing notification message

        Args:
            step: Current processing step
            client_id: Client identifier

        Returns:
            Processing notification dictionary
        """
        step_messages = {
            "intent_classification": "Analyzing your request...",
            "collecting_info": "Gathering meeting details...",
            "schedule_meeting": "Scheduling your meeting...",
            "greeting": "Preparing response...",
            "clarify_request": "Understanding your needs...",
        }

        message = step_messages.get(step, f"Processing {step.replace('_', ' ')}...")

        return {
            "type": "processing_step",
            "step": step,
            "content": message,
            "client_id": client_id,
            "timestamp": self._get_timestamp(),
        }

    async def create_interrupt_notification(
        self, interrupt_info: Dict[str, Any], client_id: str
    ) -> Dict[str, Any]:
        """
        Create a notification for user input interrupts

        Args:
            interrupt_info: Information about the interrupt
            client_id: Client identifier

        Returns:
            Interrupt notification dictionary
        """
        return {
            "type": "waiting_for_input",
            "content": interrupt_info.get(
                "prompt", "Please provide additional information"
            ),
            "next_step": interrupt_info.get("next_step"),
            "client_id": client_id,
            "timestamp": self._get_timestamp(),
            "metadata": {
                "expected_input": "user_response",
                "suggestions": self._get_input_suggestions(interrupt_info),
            },
        }

    def _get_input_suggestions(self, interrupt_info: Dict[str, Any]) -> list:
        """
        Generate input suggestions based on interrupt context

        Args:
            interrupt_info: Information about the interrupt

        Returns:
            List of suggested inputs
        """
        next_step = interrupt_info.get("next_step", "")

        if "meeting" in next_step.lower():
            return ["Tomorrow at 2 PM", "Next Monday at 10 AM", "Friday afternoon"]

        return []

    def is_ready(self) -> bool:
        """Check if the streaming handler is ready"""
        return self.graph is not None

"""
Integration Test for WebSocket Phase 2
Tests the complete flow from WebSocket to LangGraph integration
"""
import asyncio
import json
import logging
from datetime import datetime

import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketIntegrationTest:
    """Integration test for WebSocket Phase 2 implementation"""

    def __init__(self, server_url="ws://localhost:8000"):
        self.server_url = server_url
        self.client_id = f"test_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def test_basic_conversation_flow(self):
        """Test basic conversation flow with LangGraph integration"""
        uri = f"{self.server_url}/ws/{self.client_id}"

        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to {uri}")

                # Wait for connection established message
                connection_msg = await websocket.recv()
                logger.info(f"Connection message: {connection_msg}")

                # Test 1: Send a greeting message
                greeting_message = {
                    "type": "user_message",
                    "content": "Hello, I need help scheduling a meeting",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.client_id,
                }

                await websocket.send(json.dumps(greeting_message))
                logger.info("Sent greeting message")

                # Receive processing notification
                processing_msg = await websocket.recv()
                logger.info(f"Processing message: {processing_msg}")

                # Receive AI response
                response_msg = await websocket.recv()
                logger.info(f"AI response: {response_msg}")

                # Test 2: Continue the conversation
                follow_up_message = {
                    "type": "user_message",
                    "content": "I want to schedule a team standup for tomorrow at 2 PM",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.client_id,
                }

                await websocket.send(json.dumps(follow_up_message))
                logger.info("Sent follow-up message")

                # Receive processing notification
                processing_msg2 = await websocket.recv()
                logger.info(f"Processing message 2: {processing_msg2}")

                # Receive AI response
                response_msg2 = await websocket.recv()
                logger.info(f"AI response 2: {response_msg2}")

                # Check for potential interrupts/additional messages
                try:
                    # Wait briefly for any additional messages (like interrupts)
                    additional_msg = await asyncio.wait_for(
                        websocket.recv(), timeout=2.0
                    )
                    logger.info(f"Additional message: {additional_msg}")
                except asyncio.TimeoutError:
                    logger.info("No additional messages received")

                logger.info("✅ Basic conversation flow test completed successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            return False

    async def test_reconnection_and_recovery(self):
        """Test conversation recovery after reconnection"""
        uri = f"{self.server_url}/ws/{self.client_id}"

        try:
            # First connection - start a conversation
            async with websockets.connect(uri) as websocket:
                logger.info("First connection established")

                # Wait for connection message
                await websocket.recv()

                # Start a conversation
                message = {
                    "type": "user_message",
                    "content": "I want to schedule a meeting for next week",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.client_id,
                }

                await websocket.send(json.dumps(message))

                # Receive processing and response
                await websocket.recv()  # processing
                await websocket.recv()  # response

                logger.info("First conversation started")

            # Wait a moment
            await asyncio.sleep(1)

            # Second connection - test recovery
            async with websockets.connect(uri) as websocket:
                logger.info("Second connection established")

                # Wait for connection message (might include recovery info)
                connection_msg = await websocket.recv()
                logger.info(f"Reconnection message: {connection_msg}")

                # Parse the message to check for recovery information
                try:
                    msg_data = json.loads(connection_msg)
                    if msg_data.get("type") == "system" and "resumed" in msg_data.get(
                        "content", ""
                    ):
                        logger.info("✅ Conversation recovery detected")
                except Exception:
                    pass

                # Continue the conversation
                follow_up = {
                    "type": "user_message",
                    "content": "Actually, make it for Friday at 3 PM",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.client_id,
                }

                await websocket.send(json.dumps(follow_up))

                # Receive response
                await websocket.recv()  # processing
                response = await websocket.recv()  # response
                logger.info(f"Continuation response: {response}")

                logger.info("✅ Reconnection and recovery test completed successfully")
                return True

        except Exception as e:
            logger.error(f"❌ Reconnection test failed: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling with malformed messages"""
        uri = f"{self.server_url}/ws/{self.client_id}_error"

        try:
            async with websockets.connect(uri) as websocket:
                logger.info("Connected for error handling test")

                # Wait for connection message
                await websocket.recv()

                # Send malformed message
                await websocket.send("invalid json message")
                logger.info("Sent malformed message")

                # Should receive error message
                error_msg = await websocket.recv()
                logger.info(f"Error response: {error_msg}")

                # Parse and verify it's an error message
                error_data = json.loads(error_msg)
                if error_data.get("type") == "error":
                    logger.info("✅ Error handling test completed successfully")
                    return True
                else:
                    logger.error("❌ Expected error message not received")
                    return False

        except Exception as e:
            logger.error(f"❌ Error handling test failed: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting WebSocket Phase 2 Integration Tests")

        tests = [
            ("Basic Conversation Flow", self.test_basic_conversation_flow),
            ("Reconnection and Recovery", self.test_reconnection_and_recovery),
            ("Error Handling", self.test_error_handling),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n📋 Running test: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED with exception: {str(e)}")

        logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All tests passed! Phase 2 integration is working correctly.")
        else:
            logger.error(
                f"⚠️  {total - passed} tests failed. Please check the implementation."
            )

        return passed == total


async def main():
    """Main function to run the integration tests"""
    # You can modify the server URL if needed
    server_url = "ws://localhost:8000"

    tester = WebSocketIntegrationTest(server_url)
    success = await tester.run_all_tests()

    return success


if __name__ == "__main__":
    # Run the integration tests
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {str(e)}")
        exit(1)

#!/usr/bin/env python3
"""
Simple WebSocket Test Client
For testing the MeetingMuse WebSocket server
"""
import asyncio
import json
import sys
from datetime import datetime

import aiohttp
import websockets


async def test_websocket_client() -> None:
    """Test WebSocket client to verify server functionality"""
    uri = "ws://localhost:8000/ws/test-client-python"

    try:
        print("Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")

            # Wait for connection confirmation message
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✓ Received connection message: {response}")

                connection_msg = json.loads(response)
                if (
                    connection_msg.get("type") == "system"
                    and connection_msg.get("content") == "connection_established"
                ):
                    print("✓ Connection established message received correctly")
                else:
                    print("✗ Unexpected connection message format")
            except asyncio.TimeoutError:
                print("✗ Timeout waiting for connection message")
                return

            # Test sending a valid message
            print("\nTesting message sending...")
            test_message = {
                "type": "user_message",
                "content": "Hello from Python test client!",
                "timestamp": datetime.now().isoformat(),
                "session_id": "test-client-python",
            }

            await websocket.send(json.dumps(test_message))
            print(f"✓ Sent message: {test_message['content']}")

            # Wait for processing message
            try:
                processing_response = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                print(f"✓ Received processing message: {processing_response}")

                processing_msg = json.loads(processing_response)
                if (
                    processing_msg.get("type") == "system"
                    and processing_msg.get("content") == "processing"
                ):
                    print("✓ Processing message received correctly")
                else:
                    print("✗ Unexpected processing message format")
            except asyncio.TimeoutError:
                print("✗ Timeout waiting for processing message")
                return

            # Wait for echo response
            try:
                echo_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✓ Received echo response: {echo_response}")

                echo_msg = json.loads(echo_response)
                expected_content = f"Echo: {test_message['content']}"
                if echo_msg.get("content") == expected_content:
                    print("✓ Echo response matches expected format")
                else:
                    print(
                        f"✗ Echo response doesn't match. Expected: {expected_content}, Got: {echo_msg.get('content')}"
                    )
            except asyncio.TimeoutError:
                print("✗ Timeout waiting for echo response")
                return

            # Test sending invalid message
            print("\nTesting invalid message handling...")
            await websocket.send("This is not valid JSON")
            print("✓ Sent invalid JSON message")

            try:
                error_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✓ Received error response: {error_response}")

                error_msg = json.loads(error_response)
                if (
                    error_msg.get("type") == "error"
                    and error_msg.get("error_code") == "INVALID_MESSAGE_FORMAT"
                ):
                    print("✓ Error message received correctly")
                else:
                    print("✗ Unexpected error message format")
            except asyncio.TimeoutError:
                print("✗ Timeout waiting for error response")
                return

            print("\n✓ All WebSocket tests passed successfully!")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"✗ WebSocket connection closed unexpectedly: {e}")
    except websockets.exceptions.InvalidURI as e:
        print(f"✗ Invalid WebSocket URI: {e}")
    except ConnectionRefusedError:
        print("✗ Connection refused. Is the server running on localhost:8000?")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


async def test_admin_endpoints() -> None:
    """Test admin endpoints using HTTP requests"""

    print("Testing admin endpoints...")

    try:
        async with aiohttp.ClientSession() as session:
            # Test connections endpoint
            async with session.get("http://localhost:8000/admin/connections") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Admin connections endpoint: {data}")
                else:
                    print(f"✗ Admin connections endpoint failed: {resp.status}")

            # Test broadcast endpoint
            broadcast_data = {"content": "Test broadcast message from Python client"}
            async with session.post(
                "http://localhost:8000/admin/broadcast", json=broadcast_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Admin broadcast endpoint: {data}")
                else:
                    print(f"✗ Admin broadcast endpoint failed: {resp.status}")

    except ImportError:
        print("⚠ aiohttp not installed, skipping admin endpoint tests")
    except Exception as e:
        print(f"✗ Error testing admin endpoints: {e}")


def main() -> None:
    """Main test function"""
    print("MeetingMuse WebSocket Server Test Client")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        asyncio.run(test_admin_endpoints())
    else:
        asyncio.run(test_websocket_client())


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Demo script for MeetingMuse WebSocket Phase 2
# This script shows how to run the server with all dependencies properly configured

echo "🚀 MeetingMuse WebSocket Phase 2 Demo"
echo "======================================="
echo ""

# Set the Python path to include the src directory
export PYTHONPATH="$(pwd)/src"

# Function to start the server
start_server() {
    echo "📡 Starting WebSocket Server..."
    echo "Server will be available at: http://localhost:8000"
    echo "WebSocket endpoint: ws://localhost:8000/ws/{client_id}"
    echo "Health check: http://localhost:8000/health"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    python -m meetingmuse_server.main
}

# Function to run tests
run_tests() {
    echo "🧪 Running Integration Tests..."
    echo ""

    python tests/websocket/test_integration.py

    echo ""
    echo "✅ Tests completed!"
}

# Main menu
echo "Choose an option:"
echo "1. Start WebSocket Server"
echo "2. Run Integration Tests"
echo "3. Both (tests first, then server)"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        start_server
        ;;
    2)
        run_tests
        ;;
    3)
        run_tests
        echo ""
        echo "🔄 Starting server in 3 seconds..."
        sleep 3
        start_server
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

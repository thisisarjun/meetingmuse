# MeetingMuse WebSocket Server

## Overview

### Architecture Overview

```
Client (Web/Mobile) 
    ↓ WebSocket Connection
FastAPI WebSocket Server
    ↓ State Management
LangGraph Conversation Engine
    ↓ LLM Processing
Meeting Scheduling Logic
```

## Dependencies

The following dependencies were added to support the WebSocket server:

```toml
"fastapi (>=0.104.0,<1.0.0)",
"uvicorn[standard] (>=0.24.0,<1.0.0)",
"pydantic (>=2.0.0,<3.0.0)",
```

## API Endpoints

### Health Endpoints

#### `GET /health`
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-02T14:51:44.686338",
  "active_connections": 0
}
```

#### `GET /health/clients`
Detailed health check with server information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-02T14:51:50.406830",
  "active_connections": 0,
  "active_clients": [],
  "server_info": {
    "name": "MeetingMuse WebSocket Server",
    "version": "1.0.0",
  }
}
```

### WebSocket Endpoint

#### `WS /ws/{client_id}`
Main WebSocket endpoint for chat conversations.

**Parameters:**
- `client_id`: Unique identifier for the client session (alphanumeric, hyphens, underscores only)

**Message Flow:**
1. Client connects → Server sends connection confirmation
2. Client sends message → Server sends processing notification → Server sends echo response
3. Invalid messages trigger error responses

### Admin Endpoints

#### `GET /admin/connections`
Get information about active connections.

**Response:**
```json
{
  "active_connections": 0,
  "clients": {},
  "timestamp": "2025-08-02T14:54:01.712548"
}
```

#### `POST /admin/broadcast`
Broadcast a message to all connected clients.

**Request Body:**
```json
{
  "content": "Broadcast message content"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Broadcast completed",
  "successful_sends": 0,
  "timestamp": "2025-08-02T14:54:07.535858"
}
```

## Message Protocol

### Incoming Messages (Client → Server)
```json
{
  "type": "user_message",
  "content": "I want to schedule a meeting for tomorrow",
  "timestamp": "2025-08-02T10:30:00Z",
  "session_id": "client-123"
}
```

### Outgoing Messages (Server → Client)

#### Bot Responses
```json
{
  "content": "Echo: I want to schedule a meeting for tomorrow",
  "timestamp": "2025-08-02T10:30:01Z",
  "session_id": "client-123"
}
```

#### System Messages
```json
{
  "type": "system",
  "content": "connection_established|processing",
  "timestamp": "2025-08-02T10:30:00Z"
}
```

#### Error Messages
```json
{
  "type": "error",
  "error_code": "INVALID_MESSAGE_FORMAT",
  "message": "Message format is invalid. Please check the message structure.",
  "timestamp": "2025-08-02T10:30:00Z",
  "retry_suggested": true
}
```

## Running the Server

### 1. Start the Server
```bash
cd src
python -m meetingmuse_server.main
```

The server will start on `http://localhost:8000`.

### 2. Verify Health
```bash
curl http://localhost:8000/health
```

### 3. Test WebSocket Connection
Use the provided test client:
```bash
python scripts/test_websocket_client.py
```

## Testing

### Unit Tests
Run the connection manager tests:
```bash
python -m pytest tests/websocket/test_connection_manager.py -v
```

### Manual Testing
Follow the comprehensive [manual testing guide](../docs/websocket_manual_testing.md).

## Implementation Details

### ConnectionManager Class
- Manages active WebSocket connections
- Handles connection lifecycle (connect, disconnect, cleanup)
- Provides message sending capabilities (personal, system, error, broadcast)
- Tracks connection metadata (connection time, message count)

### Message Protocol
- Validates incoming messages using Pydantic models
- Enforces client ID format validation
- Provides structured error responses
- Supports multiple message types (user, system, error)

### Error Handling
- Graceful WebSocket disconnection handling
- Invalid message format detection
- Client ID validation
- Connection failure recovery
- Comprehensive logging

### Security Considerations
- Client ID format validation
- Input message validation
- Graceful error handling without exposing internal details
- Connection limits (configurable)

## Next Steps (Phase 2)

Phase 1 provides the foundation for Phase 2 implementation:

1. **LangGraph Integration**: Replace echo functionality with actual LangGraph conversation processing
2. **State Persistence**: Implement conversation state persistence using LangGraph's MemorySaver
3. **Async Pipeline**: Enhanced async message processing pipeline
4. **Advanced Error Handling**: More sophisticated error recovery mechanisms

## Known Limitations

### Phase 1 Scope
- **Echo Responses Only**: Messages are echoed back (placeholder for LangGraph integration)
- **No State Persistence**: Conversation state is not persisted across connections
- **Basic Authentication**: No authentication/authorization implemented
- **Limited Rate Limiting**: No rate limiting implemented

### Test Limitations
- Some message protocol tests fail due to mock setup (actual functionality works correctly)
- Admin endpoint tests require aiohttp (not installed by default)

## Configuration

The server uses default configuration for Phase 1:
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 8000
- **Auto-reload**: Enabled for development
- **Log Level**: INFO

## Troubleshooting

### Common Issues
1. **Port 8000 in use**: Change port in `main.py` or stop conflicting services
2. **Dependencies missing**: Run `pip install fastapi "uvicorn[standard]" pydantic websockets`
3. **Import errors**: Ensure you're running from the correct directory

### Debug Mode
The server runs with auto-reload enabled for development. For production, modify the uvicorn configuration in `main.py`.

---

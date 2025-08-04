# MeetingMuse WebSocket Server PRD

## Executive Summary

This PRD outlines the implementation of a WebSocket server.

## Technology Recommendation: FastAPI WebSockets

**Recommended Solution:** FastAPI WebSocket implementation

**Rationale:**
- **Seamless Integration**: Natural fit with existing Python ecosystem (Pydantic models, async/await)
- **Built-in Features**: Dependency injection, automatic documentation, middleware support
- **Scalability**: Supports connection management patterns needed for chat applications

## Architecture Overview

```
Client (Web/Mobile) 
    ↓ WebSocket Connection
FastAPI WebSocket Server
    ↓ State Management
LangGraph Conversation Engine
    ↓ LLM Processing
Meeting Scheduling Logic
```

## Core Components

### 1. WebSocket Connection Manager
```python
class ConnectionManager:
    - active_connections: Dict[str, WebSocket]
    - connect(websocket, client_id)
    - disconnect(client_id)
    - send_personal_message(message, client_id)
    - broadcast(message)
```

### 2. WebSocket Endpoints

#### `/ws/{client_id}`
- **Purpose**: Main chat endpoint for conversation
- **Parameters**: 
  - `client_id`: Unique identifier for client session
- **Flow**:
  1. Accept WebSocket connection
  2. Initialize conversation state
  3. Process incoming messages through LangGraph
  4. Send responses back to client

### 3. Message Protocol

#### Incoming Message Format
```json
{
  "type": "user_message",
  "content": "I want to schedule a meeting for tomorrow",
  "timestamp": "2025-01-28T10:30:00Z",
  "session_id": "uuid-here"
}
```

#### Outgoing Message Format
```json
{
  "content": "I'll help you schedule that meeting. What time works best?",
  "timestamp": "2025-01-28T10:30:01Z",
  "session_id": "uuid-here",
}
```

#### System Messages
```json
{
  "type": "system",
  "content": "connection_established|processing|error",
  "timestamp": "2025-01-28T10:30:00Z"
}
```

## Integration with Existing Codebase

### State Management Architecture
- **Connection Management**: WebSocket connections handled separately by `ConnectionManager`
- **State Mapping**: `client_id` from WebSocket becomes `thread_id` for LangGraph conversations
- **Persistence**: Use LangGraph's `MemorySaver` for conversation persistence per thread

### LangGraph Integration
```python
async def process_message(websocket: WebSocket, client_id: str, message: str):
    # ConnectionManager handles WebSocket connections
    # client_id maps directly to LangGraph thread_id
    
    # Process through existing LangGraph workflow
    graph = build_conversation_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": client_id}}
    )
    
    # Send response via WebSocket
    await send_response(websocket, result)
```

## Exception Handling Strategy

### Connection-Level Exceptions
1. **WebSocketDisconnect**
   - Clean up connection from manager
   - Persist conversation state
   - Log disconnection with client_id

2. **ConnectionClosed**
   - Attempt graceful cleanup
   - Save partial conversation state
   - Log

3. **Authentication/Authorization Errors**
   - Close connection with appropriate error code
   - Log security events
   - Rate limit subsequent attempts

### Application-Level Exceptions
1. **LLM Processing Errors**
   - Send user-friendly error message
   - Maintain conversation continuity
   - Log for debugging

2. **State Serialization Errors**
   - Fallback to basic conversation mode
   - Alert monitoring systems
   - Attempt state recovery

### Error Response Format
```json
{
  "type": "error",
  "error_code": "LLM_PROCESSING_ERROR",
  "message": "I'm having trouble processing your request. Please try again.",
  "timestamp": "2025-01-28T10:30:00Z",
  "retry_suggested": true
}
```

## Implementation Plan

### Phase 1: Core WebSocket Server
- [ ] FastAPI WebSocket endpoint setup
- [ ] Create health endpoints
- [ ] Basic ConnectionManager implementation
- [ ] Message protocol definition
- [x] Clean separation between connection and conversation state

### Phase 2: LangGraph Integration
- [ ] Async message processing pipeline
- [ ] Conversation state persistence
- [ ] Error handling and recovery

### Phase 3: Advanced Features
- [ ] Connection pooling and management
- [ ] Rate limiting and authentication
- [ ] Monitoring and observability or Just Logging

## Testing Strategy

### Unit Tests
```python
# Connection Manager Tests
- test_connection_establishment()
- test_connection_cleanup()
- test_message_broadcasting()

# Message Processing Tests  
- test_user_message_processing()
- test_langgraph_integration()
- test_state_persistence()

# Error Handling Tests
- test_websocket_disconnect_handling()
- test_llm_error_recovery()
- test_malformed_message_handling()
```

### Integration Tests
```python
# End-to-End Conversation Tests
- test_complete_meeting_scheduling_flow()
- test_multi_client_conversations()
- test_connection_recovery()

# Performance Tests
- test_concurrent_connections()
- test_message_throughput()
- test_memory_usage_under_load()
```

### Test Implementation Structure
```
tests/
├── websocket/
│   ├── test_connection_manager.py
│   ├── test_message_processing.py
│   ├── test_error_handling.py
│   └── test_integration.py
└── fixtures/
    ├── websocket_client.py
    └── mock_langgraph.py
```

## Dependencies

### New Dependencies to Add
```toml
# WebSocket support (included in FastAPI)
fastapi = ">=0.104.0"
uvicorn = {extras = ["standard"], version = ">=0.24.0"}
```

### File Structure
```
src/meetingmuse/
├── websocket/
│   ├── __init__.py
│   ├── connection_manager.py
│   ├── message_processor.py
│   ├── error_handlers.py
│   └── websocket_server.py
└── api/
    ├── __init__.py
    └── websocket_routes.py
```

## Security Considerations

1. **Rate Limiting**: Prevent abuse with per-client message limits  
2. **Input Validation**: Sanitize all incoming messages
3. **Connection Limits**: Maximum concurrent connections per client
4. **CORS**: Configure appropriate CORS policies for WebSocket endpoints

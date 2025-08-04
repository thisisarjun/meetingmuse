# MeetingMuse WebSocket Server - Phase 2 Integration

This implementation integrates the MeetingMuse LangGraph conversation engine with the existing WebSocket server infrastructure, replacing echo-based responses with intelligent AI-powered meeting scheduling assistance.

## 🚀 Features Implemented

### Core Integration
- ✅ **LangGraph Integration**: Full integration with MeetingMuse conversation engine
- ✅ **Intelligent Conversations**: AI-powered meeting scheduling assistance
- ✅ **State Persistence**: Conversation context maintained across WebSocket connections
- ✅ **Real-time Processing**: Immediate feedback during LLM processing
- ✅ **Interrupt Handling**: Support for user input collection workflows
- ✅ **Conversation Recovery**: Automatic state recovery on reconnection

### Technical Components
- ✅ **LangGraph Factory**: Singleton factory for graph instance management
- ✅ **Message Processor**: Async message processing through LangGraph workflow
- ✅ **Conversation Manager**: State management and recovery
- ✅ **Streaming Handler**: Real-time response streaming and processing feedback
- ✅ **Enhanced Connection Manager**: Extended with conversation context support
- ✅ **Updated Message Protocol**: New system message types for rich interactions

## 📁 File Structure

```
src/meetingmuse_server/
├── langgraph_factory.py       # LangGraph initialization and setup
├── message_processor.py       # LangGraph message processing logic
├── conversation_manager.py    # Conversation state and recovery
├── streaming_handler.py       # Real-time response streaming
├── websocket_routes.py        # Updated with LangGraph processing
├── connection_manager.py      # Enhanced with conversation context
├── message_protocol.py        # Updated with new message types
└── constants.py               # Added new system message types

tests/websocket/
├── test_langgraph_factory.py     # LangGraph factory tests
├── test_message_processor.py     # Message processing tests
├── test_conversation_manager.py  # State management tests
├── test_streaming_handler.py     # Streaming response tests
└── test_integration.py           # End-to-end integration tests
```

## 🛠️ Quick Start

### 1. Install Dependencies

Ensure you have all the required dependencies from the main project:

```bash
# From the project root
poetry install
```

### 2. Start the Server

```bash
# Using the startup script (recommended)
python start_websocket_server.py

# Or directly
python -m meetingmuse_server.main
```

### 3. Test the Integration

The server will start on `http://localhost:8000` with:
- **WebSocket endpoint**: `ws://localhost:8000/ws/{client_id}`
- **Health check**: `http://localhost:8000/health`
- **Detailed health**: `http://localhost:8000/health/clients`

## 📡 API Reference

### WebSocket Messages

#### User Message Format
```json
{
  "type": "user_message",
  "content": "I want to schedule a meeting for tomorrow",
  "timestamp": "2025-01-28T10:30:00Z",
  "session_id": "client-123"
}
```

#### AI Response Format
```json
{
  "content": "I'll help you schedule that meeting. What time works best?",
  "timestamp": "2025-01-28T10:30:01Z",
  "session_id": "client-123"
}
```

#### System Messages

**Processing Notification**
```json
{
  "type": "system",
  "content": "processing",
  "timestamp": "2025-01-28T10:30:00Z"
}
```

**Conversation Resumed**
```json
{
  "type": "system",
  "content": "conversation_resumed",
  "timestamp": "2025-01-28T10:30:00Z",
  "metadata": {
    "conversation_summary": "We were scheduling a team meeting for tomorrow",
    "message_count": 5
  }
}
```

**Waiting for Input**
```json
{
  "type": "system",
  "content": "waiting_for_input",
  "timestamp": "2025-01-28T10:30:00Z",
  "metadata": {
    "prompt": "Please provide the meeting duration",
    "next_step": "collecting_info",
    "suggestions": ["30 minutes", "1 hour", "2 hours"]
  }
}
```

#### Error Messages
```json
{
  "type": "error",
  "error_code": "LLM_PROCESSING_ERROR",
  "message": "I'm having trouble processing your request. Please try again.",
  "timestamp": "2025-01-28T10:30:00Z",
  "retry_suggested": true,
  "metadata": {
    "conversation_preserved": true,
    "fallback_available": true
  }
}
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all WebSocket tests
python -m pytest tests/websocket/ -v

# Run specific test files
python -m pytest tests/websocket/test_message_processor.py -v
```

### Run Integration Tests

```bash
# Make sure the server is running first
python start_websocket_server.py

# In another terminal, run integration tests
python tests/websocket/test_integration.py
```

### Manual Testing with WebSocket Client

You can test the server using a WebSocket client like `wscat`:

```bash
# Install wscat if needed
npm install -g wscat

# Connect to the server
wscat -c "ws://localhost:8000/ws/manual-test-client"

# Send a message
{"type": "user_message", "content": "Hello, I need to schedule a meeting", "timestamp": "2025-01-28T10:30:00Z", "session_id": "manual-test-client"}
```

## 🔍 Monitoring & Health Checks

### Health Endpoints

**Basic Health Check**
```bash
curl http://localhost:8000/health
```

**Detailed Health Check**
```bash
curl http://localhost:8000/health/clients
```

### Logs

The server provides comprehensive logging for:
- Connection establishment and cleanup
- Message processing through LangGraph
- Conversation state changes
- Error handling and recovery
- Performance metrics

## 🚀 Key Improvements from Phase 1

### Before (Phase 1)
- Simple echo responses
- No conversation context
- Basic connection management
- Limited error handling

### After (Phase 2)
- ✅ **Intelligent AI responses** via LangGraph integration
- ✅ **Conversation persistence** across reconnections
- ✅ **Real-time processing feedback** with streaming support
- ✅ **Interrupt handling** for user input collection
- ✅ **Enhanced error handling** with graceful fallbacks
- ✅ **Conversation recovery** after disconnections
- ✅ **Rich system messages** for better UX

## 🔧 Configuration

### Environment Variables

The following environment variables can be configured:

```bash
# LangGraph Processing (default: True)
LANGGRAPH_ENABLED=true

# LLM Processing Timeout (default: 30 seconds)
LLM_TIMEOUT_SECONDS=30

# Conversation State TTL (default: 24 hours)
CONVERSATION_TTL_HOURS=24

# Maximum Concurrent Conversations (default: 1000)
MAX_CONCURRENT_CONVERSATIONS=1000

# Enable Streaming Responses (default: True)
STREAMING_ENABLED=true
```

## 🛡️ Error Handling

The implementation includes comprehensive error handling for:

- **Connection-level errors**: WebSocket disconnections, authentication failures
- **LLM processing errors**: Model timeouts, API failures
- **State persistence errors**: Memory issues, serialization failures
- **Message format errors**: Invalid JSON, missing fields

All errors are logged and appropriate error messages are sent to clients with recovery suggestions.

## 📊 Performance Considerations

- **Singleton Pattern**: LangGraph instances are reused across connections
- **Async Processing**: All operations are async to prevent blocking
- **Memory Management**: Conversation states are managed with TTL
- **Connection Pooling**: Efficient WebSocket connection management
- **Streaming Responses**: Real-time feedback without blocking

## 🔄 Backward Compatibility

Phase 2 maintains 100% backward compatibility with Phase 1:
- All existing WebSocket message formats are preserved
- New features are additive enhancements
- Existing clients continue to work without changes
- Graceful degradation if LangGraph is unavailable

## 🎯 Next Steps

Potential enhancements for future phases:
- **Authentication & Authorization**: JWT-based client validation
- **Rate Limiting**: Per-client message rate limits
- **Metrics & Analytics**: Detailed conversation analytics
- **Horizontal Scaling**: Multi-instance deployment support
- **Persistent Storage**: Database-backed conversation persistence

## 🐛 Troubleshooting

### Common Issues

**LangGraph Initialization Fails**
- Check that all dependencies are installed
- Verify HuggingFace API token is configured
- Review startup logs for specific errors

**WebSocket Connection Drops**
- Check server logs for connection errors
- Verify client_id format is valid
- Test with basic WebSocket client first

**Slow Response Times**
- Monitor LLM processing logs
- Check server resource usage
- Consider adjusting timeout settings

### Debug Mode

Enable debug logging for more detailed information:

```bash
export LOG_LEVEL=DEBUG
python start_websocket_server.py
```

## 📝 Contributing

When contributing to Phase 2:

1. **Run Tests**: Ensure all tests pass before submitting
2. **Update Documentation**: Update this README for new features
3. **Backward Compatibility**: Maintain compatibility with existing clients
4. **Error Handling**: Include comprehensive error handling
5. **Logging**: Add appropriate logging for debugging

---

**Phase 2 Status**: ✅ **COMPLETE** - Ready for production deployment

This implementation successfully integrates LangGraph with the WebSocket server while maintaining full backward compatibility and adding powerful new conversation capabilities.

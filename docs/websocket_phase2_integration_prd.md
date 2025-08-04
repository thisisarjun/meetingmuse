# MeetingMuse WebSocket Server - Phase 2 Integration PRD

## Executive Summary

This PRD outlines the integration of the existing MeetingMuse LangGraph conversation engine with the Phase 1 WebSocket server infrastructure. The integration will replace the current echo-based message handling with intelligent conversation processing while maintaining all existing WebSocket functionality.

## Business Objectives

### Primary Goals
1. **Intelligent Conversations**: Replace echo responses with contextual, AI-powered meeting scheduling assistance
2. **State Persistence**: Maintain conversation context across WebSocket connections
3. **Real-time Processing**: Provide immediate feedback during LLM processing
4. **Seamless Experience**: Zero disruption to existing WebSocket client functionality

### Success Metrics
- ✅ All existing WebSocket functionality preserved
- ✅ Conversation state persists across reconnections
- ✅ Response time < 3 seconds for typical queries
- ✅ Support for interrupted workflows (user input collection)
- ✅ 100% backward compatibility with Phase 1 API

## Current State Analysis

### Phase 1 Achievements
- ✅ Robust WebSocket server with FastAPI
- ✅ Connection management and message protocol
- ✅ Health and admin endpoints
- ✅ Comprehensive error handling
- ✅ Production-ready logging

### Phase 1 Limitations
- 🔄 Echo-only responses (placeholder functionality)
- 🔄 No conversation context or memory
- 🔄 No intelligent intent recognition
- 🔄 Limited meeting scheduling capabilities

## Technical Architecture

### System Overview
```
┌─────────────────┐    WebSocket     ┌─────────────────────┐
│   Client Apps   │ ◄─────────────► │ meetingmuse_server  │
│                 │   (JSON msgs)    │                     │
└─────────────────┘                  └─────────────────────┘
                                               │
                     Integration Layer         │
                                               ▼
                                    ┌─────────────────────┐
                                    │   meetingmuse       │
                                    │  (LangGraph Core)   │
                                    │                     │
                                    │ • Graph Builder     │
                                    │ • Conversation Nodes│
                                    │ • Intent Classifier │
                                    │ • State Management  │
                                    │ • LLM Integration   │
                                    └─────────────────────┘
```

### Integration Points

#### 1. Thread ID Mapping
```python
# Direct 1:1 mapping (no changes needed)
WebSocket client_id ←→ LangGraph thread_id
```

#### 2. Message Processing Pipeline
```
User Message → WebSocket Server → LangGraph Processing → AI Response → WebSocket Client
     ↓                ↓                    ↓                ↓              ↓
JSON Validation → Message Protocol → Graph Execution → Response Format → Real-time Delivery
```

#### 3. State Persistence
```python
# LangGraph's MemorySaver handles all persistence
checkpointer = MemorySaver()  # Already implemented in meetingmuse
config = {"configurable": {"thread_id": client_id}}
```

## Feature Specifications

### 1. LangGraph Message Processing

#### Current (Phase 1)
```python
# Simple echo response
response_content = f"Echo: {user_message.content}"
await connection_manager.send_personal_message(response_content, client_id)
```

#### New (Phase 2)
```python
# Intelligent LangGraph processing
async def process_with_langgraph(message: str, client_id: str):
    input_data = {"messages": [HumanMessage(content=message)]}
    config = {"configurable": {"thread_id": client_id}}

    # Process through LangGraph workflow
    result = await graph.ainvoke(input_data, config=config)

    # Extract AI response
    ai_message = result["messages"][-1]
    return ai_message.content
```

### 2. Streaming Response Support

#### Real-time Processing Feedback
```python
# Send processing notification
await connection_manager.send_system_message(client_id, "processing")

# Stream LangGraph execution steps
async for chunk in graph.astream(input_data, config=config):
    if chunk.get("messages"):
        latest_message = chunk["messages"][-1]
        if latest_message.type == "ai":
            await connection_manager.send_personal_message(
                latest_message.content, client_id
            )
```

### 3. Interrupt Handling

#### User Input Collection
```python
# Handle LangGraph interrupts for user input
current_state = graph.get_state(config)
if current_state.next:  # Graph is interrupted and waiting
    await connection_manager.send_system_message(
        client_id,
        "waiting_for_input",
        additional_data={
            "prompt": "Please provide additional meeting details",
            "next_step": current_state.next[0]
        }
    )
```

### 4. Conversation Context

#### State Recovery
```python
# Automatic state recovery on reconnection
async def handle_reconnection(client_id: str):
    config = {"configurable": {"thread_id": client_id}}
    current_state = graph.get_state(config)

    if current_state.values:
        # Send conversation summary
        await connection_manager.send_system_message(
            client_id,
            "conversation_resumed",
            summary=generate_conversation_summary(current_state)
        )
```

## Implementation Plan

### Phase 2.1: Core Integration (Week 1)
- [ ] Create LangGraph factory in `meetingmuse_server`
- [ ] Replace echo logic with LangGraph processing
- [ ] Implement basic async message handling
- [ ] Add conversation state initialization

### Phase 2.2: Advanced Features (Week 2)
- [ ] Implement streaming responses
- [ ] Add interrupt handling for user input collection
- [ ] Create conversation recovery mechanisms
- [ ] Enhanced error handling for LLM failures

### Phase 2.3: Optimization & Testing (Week 3)
- [ ] Performance optimization
- [ ] Comprehensive testing suite
- [ ] Load testing with multiple concurrent conversations
- [ ] Documentation updates

## File Structure Changes

### New Files to Create
```
src/meetingmuse_server/
├── langgraph_factory.py       # LangGraph initialization and setup
├── message_processor.py       # LangGraph message processing logic
├── conversation_manager.py    # Conversation state and recovery
└── streaming_handler.py       # Real-time response streaming
```

### Files to Modify
```
src/meetingmuse_server/
├── websocket_routes.py        # Replace echo with LangGraph processing
├── connection_manager.py      # Add conversation context methods
└── message_protocol.py        # Add new system message types
```

## API Enhancements

### New System Message Types

#### Conversation State Messages
```json
{
  "type": "system",
  "content": "conversation_resumed",
  "timestamp": "2025-08-02T10:30:00Z",
  "metadata": {
    "conversation_summary": "Scheduling meeting for tomorrow at 2 PM",
    "pending_actions": ["confirm_attendees"]
  }
}
```

#### Processing Status Messages
```json
{
  "type": "system",
  "content": "processing_step",
  "timestamp": "2025-08-02T10:30:00Z",
  "metadata": {
    "step": "intent_classification",
    "progress": "Analyzing your request..."
  }
}
```

#### Input Collection Messages
```json
{
  "type": "system",
  "content": "waiting_for_input",
  "timestamp": "2025-08-02T10:30:00Z",
  "metadata": {
    "prompt": "Please provide the meeting duration",
    "expected_input": "duration",
    "suggestions": ["30 minutes", "1 hour", "2 hours"]
  }
}
```

### Enhanced Error Handling

#### LLM Processing Errors
```json
{
  "type": "error",
  "error_code": "LLM_PROCESSING_ERROR",
  "message": "I'm having trouble processing your request. Please try again.",
  "timestamp": "2025-08-02T10:30:00Z",
  "retry_suggested": true,
  "metadata": {
    "conversation_preserved": true,
    "fallback_available": true
  }
}
```

## Integration Implementation Details

### 1. LangGraph Factory Pattern
```python
# src/meetingmuse_server/langgraph_factory.py
class LangGraphFactory:
    @staticmethod
    def create_conversation_graph():
        """Initialize and return configured LangGraph instance"""
        # Import meetingmuse components
        from meetingmuse.graph import GraphBuilder
        from meetingmuse.models.state import MeetingMuseBotState
        # ... initialize all components

        return graph_builder.compile(
            interrupt_after=[NodeName.COLLECTING_INFO],
            checkpointer=MemorySaver()
        )
```

### 2. Async Message Processing
```python
# src/meetingmuse_server/message_processor.py
class LangGraphMessageProcessor:
    async def process_user_message(self, content: str, client_id: str) -> str:
        """Process user message through LangGraph workflow"""

    async def handle_interrupts(self, client_id: str) -> bool:
        """Handle LangGraph interrupts for user input"""

    async def get_conversation_state(self, client_id: str) -> dict:
        """Get current conversation state"""
```

### 3. WebSocket Route Updates
```python
# Enhanced WebSocket message handling
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # ... existing connection logic

    while True:
        message_text = await websocket.receive_text()
        user_message = MessageProtocol.parse_user_message(message_text)

        # NEW: Process through LangGraph instead of echo
        await connection_manager.send_system_message(client_id, "processing")

        try:
            response = await message_processor.process_user_message(
                user_message.content, client_id
            )
            await connection_manager.send_personal_message(response, client_id)

            # Handle any interrupts
            await message_processor.handle_interrupts(client_id)

        except LLMProcessingError as e:
            await connection_manager.send_error_message(
                client_id, "LLM_PROCESSING_ERROR", str(e)
            )
```

## Testing Strategy

### Unit Tests
```python
# New test files to create
tests/websocket/
├── test_langgraph_factory.py     # LangGraph initialization tests
├── test_message_processor.py     # Message processing tests
├── test_conversation_manager.py  # State management tests
└── test_streaming_handler.py     # Streaming response tests
```

### Integration Tests
```python
# Enhanced integration tests
- test_complete_conversation_flow()
- test_conversation_recovery_after_disconnect()
- test_interrupt_handling()
- test_concurrent_conversations()
- test_llm_error_recovery()
```

### Performance Tests
```python
# Load testing scenarios
- test_100_concurrent_conversations()
- test_conversation_memory_usage()
- test_response_time_under_load()
- test_state_persistence_performance()
```

## Risk Assessment & Mitigation

### Technical Risks

#### Risk: LLM Processing Latency
- **Impact**: Slow response times affecting user experience
- **Mitigation**:
  - Implement streaming responses for immediate feedback
  - Add processing status messages
  - Set reasonable timeout limits (30 seconds)
  - Fallback to simple responses on timeout

#### Risk: Memory Usage Growth
- **Impact**: Server memory exhaustion with many concurrent conversations
- **Mitigation**:
  - Monitor conversation state size
  - Implement conversation cleanup after inactivity
  - Add memory usage metrics to health endpoints

#### Risk: State Persistence Failures
- **Impact**: Loss of conversation context
- **Mitigation**:
  - Robust error handling in MemorySaver operations
  - Graceful degradation to stateless mode
  - Regular state persistence validation

### Operational Risks

#### Risk: Backward Compatibility
- **Impact**: Breaking existing WebSocket clients
- **Mitigation**:
  - Maintain all existing message formats
  - Add new features as optional enhancements
  - Comprehensive regression testing

#### Risk: Deployment Complexity
- **Impact**: Difficult deployments and rollbacks
- **Mitigation**:
  - Feature flags for LangGraph processing
  - Blue-green deployment strategy
  - Automated rollback procedures

## Configuration Management

### Environment Variables
```python
# New configuration options
LANGGRAPH_ENABLED = True              # Feature flag for LangGraph processing
LLM_TIMEOUT_SECONDS = 30             # Maximum LLM processing time
CONVERSATION_TTL_HOURS = 24          # Conversation state retention
MAX_CONCURRENT_CONVERSATIONS = 1000   # Resource limiting
STREAMING_ENABLED = True              # Enable streaming responses
```

### Production Configuration
```python
# Production-optimized settings
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,                        # Multi-worker for scaling
    reload=False,                     # Disable auto-reload
    access_log=True,
    log_level="info"
)
```

## Monitoring & Observability

### New Metrics to Track
```python
# Conversation metrics
- active_conversations_count
- average_conversation_length
- conversation_completion_rate
- interrupt_handling_success_rate

# Performance metrics
- llm_response_time_avg
- llm_response_time_p95
- memory_usage_per_conversation
- error_rate_by_type

# Business metrics
- successful_meeting_schedules
- user_satisfaction_by_intent
- conversation_drop_off_points
```

### Enhanced Logging
```python
# Conversation-aware logging
logger.info(
    "Conversation processed",
    extra={
        "client_id": client_id,
        "intent": user_intent,
        "response_time_ms": response_time,
        "conversation_step": current_step,
        "tokens_used": token_count
    }
)
```

## Success Criteria

### Functional Requirements
- [ ] All Phase 1 functionality preserved
- [ ] Intelligent meeting scheduling conversations
- [ ] Conversation state persistence across connections
- [ ] Real-time processing feedback
- [ ] Interrupt handling for user input collection
- [ ] Graceful error handling and recovery

### Performance Requirements
- [ ] Response time < 3 seconds for 95% of requests
- [ ] Support 100+ concurrent conversations
- [ ] Memory usage < 100MB per conversation
- [ ] 99.9% uptime during business hours

### Quality Requirements
- [ ] Zero breaking changes to existing API
- [ ] Comprehensive test coverage (>90%)
- [ ] Complete documentation updates
- [ ] Successful load testing results

## Timeline

### Week 1: Core Integration
- **Days 1-2**: LangGraph factory and basic integration
- **Days 3-4**: Replace echo logic with LangGraph processing
- **Day 5**: Initial testing and debugging

### Week 2: Advanced Features
- **Days 1-2**: Streaming response implementation
- **Days 3-4**: Interrupt handling and user input collection
- **Day 5**: Conversation recovery mechanisms

### Week 3: Testing & Documentation
- **Days 1-2**: Comprehensive testing suite
- **Days 3-4**: Performance testing and optimization
- **Day 5**: Documentation updates and deployment preparation

## Rollout Strategy

### Phase 2.1: Internal Testing
- Deploy to development environment
- Internal team testing with real conversations
- Performance benchmarking

### Phase 2.2: Limited Release
- Feature flag rollout to 10% of connections
- Monitor metrics and error rates
- Gather user feedback

### Phase 2.3: Full Deployment
- Complete rollout to all users
- Remove echo-based fallback
- Monitor production stability

---

## Conclusion

Phase 2 integration leverages the excellent architectural foundation from Phase 1 to deliver intelligent conversation capabilities with minimal risk and maximum compatibility. The clean separation between infrastructure (`meetingmuse_server`) and business logic (`meetingmuse`) enables a seamless integration that enhances functionality while preserving all existing capabilities.

**Expected Outcome**: A production-ready WebSocket server that provides intelligent, contextual meeting scheduling assistance while maintaining the robust infrastructure and reliability established in Phase 1.

# MeetingMuse Google OAuth Integration PRD

## Document Information
- **Version**: 1.0
- **Date**: August 12, 2025
- **Status**: Draft
- **Author**: GitHub Copilot
- **Project**: MeetingMuse Calendar Bot

---

## Executive Summary

This PRD outlines the implementation of Google OAuth 2.0 authentication and Google Calendar API integration for MeetingMuse, transforming it from a simulated calendar bot to a fully functional calendar management assistant with real Google Calendar access.

## Current State Analysis

### Existing Architecture
- **Framework**: FastAPI + WebSocket server with LangGraph-powered conversation flow
- **Current Implementation**: Simulated calendar operations with 30% success rate for demo purposes
- **Key Components**:
  - WebSocket-based real-time communication
  - LangGraph state machine for conversation flow
  - HuggingFace LLM integration for natural language processing
  - Node-based architecture (greeting → intent classification → info collection → scheduling)

### Current Limitations
1. **No Real Calendar Integration**: `ScheduleMeetingNode` uses simulated API calls
2. **No Authentication**: No user identity or calendar access
3. **No Persistence**: No connection to actual calendar systems
4. **Limited Functionality**: Cannot read, create, or modify real calendar events

---

## Business Objectives

### Primary Goals
1. **Enable Real Calendar Access**: Replace simulated scheduling with actual Google Calendar operations
2. **Secure Authentication**: Implement OAuth 2.0 for secure user authorization
3. **Incremental Authorization**: Request minimal permissions initially, expand as needed
4. **Enhanced User Experience**: Provide seamless calendar integration without compromising security

### Success Metrics
- **Authentication Success Rate**: >95% successful OAuth flows
- **Calendar Operation Success Rate**: >98% (replacing current 30% simulation)
- **User Adoption**: Enable real calendar management for MeetingMuse users
- **Security Compliance**: Full OAuth 2.0 implementation with appropriate scopes

---

## Technical Requirements

### 1. Google OAuth 2.0 Implementation

#### 1.1 OAuth Configuration
```python
# Required Environment Variables
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar
```

#### 1.2 OAuth Scopes Strategy
**Phase 1 - Basic Calendar Access**:
- `https://www.googleapis.com/auth/calendar.readonly` - Read calendar events
- `https://www.googleapis.com/auth/calendar.events` - Create/modify events

#### 1.3 Incremental Authorization
- Start with minimal read-only access
- Request additional permissions when needed
- Graceful degradation for partial permissions

### 2. Authentication Flow Architecture

#### 2.1 OAuth Flow Integration
```
┌─────────────────┐   1. Auth Request   ┌─────────────────────┐
│   Client App    │ ───────────────────► │ MeetingMuse Server  │
│  (Web/Mobile)   │                      │                     │
└─────────────────┘                      └─────────────────────┘
         ▲                                           │
         │                                           │ 2. Redirect to Google
         │                                           ▼
         │                                ┌─────────────────────┐
         │                                │   Google OAuth      │
         │                                │   Authorization     │
         │                                │      Server         │
         │                                └─────────────────────┘
         │                                           │
         │ 5. Authenticated                          │ 3. User Consent
         │    Session                                │
         │                                           ▼
         │ 4. Auth Callback    ┌─────────────────────┐
         └─────────────────────│ MeetingMuse Server  │
                               │   Auth Handler      │
                               └─────────────────────┘
```

#### 2.2 Session Management
- **Token Storage**: Secure server-side session storage
- **Token Refresh**: Automatic refresh token handling
- **Session Persistence**: Maintain authentication across WebSocket connections
- **Security**: Encrypted token storage with expiration handling

### 3. Google Calendar API Integration

#### 3.1 Calendar Service Architecture
```python
# New Service Layer
src/meetingmuse/services/google_calendar_service.py
src/meetingmuse/services/oauth_service.py
src/meetingmuse/models/calendar_models.py
src/server/api/auth_api.py
```

#### 3.2 Calendar Operations
**Core Operations**:
- **List Events**: Read existing calendar events
- **Create Events**: Schedule new meetings
- **Check Availability**: Find free time slots

### 4. WebSocket Authentication Integration

#### 4.1 Authenticated WebSocket Connections
```python
# Enhanced WebSocket connection with auth
@websocket_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    auth_token: str = Query(...)
):
    # Validate auth token
    # Establish authenticated session
    # Enable calendar operations
```
---

## Implementation Plan

### Phase 1: OAuth Foundation (Week 1-2)
1. **Google Cloud Setup**
   - Create Google Cloud Project
   - Enable Calendar API
   - Configure OAuth consent screen
   - Generate client credentials

2. **Backend Authentication**
   - Implement OAuth service
   - Create auth API endpoints
   - Add token management
   - Update configuration system

3. **Security Infrastructure**
   - Implement token encryption
   - Add session management
   - Configure CORS for OAuth redirects
   - Add security middleware

4. **WebSocket Integration**
   - Add authentication to WebSocket connections
   - Enable calendar operations through chat
   - Implement real-time calendar updates

### Phase 2: Calendar Integration (Week 3-4)
1. **Google Calendar Service**
   - Implement calendar API client
   - Create calendar operation methods
   - Add error handling and retries
   - Test with real Google Calendar

2. **Update Conversation Flow**
   - Replace simulated API calls in `ScheduleMeetingNode`
   - Add calendar availability checking
   - Implement real meeting creation
   - Update error handling for API failures

---

## Technical Specifications

### 1. New Dependencies
```toml
# Add to pyproject.toml
google-auth = "^2.0.0"
google-auth-oauthlib = "^1.0.0"
google-auth-httplib2 = "^0.2.0"
google-api-python-client = "^2.0.0"
cryptography = "^41.0.0"  # For token encryption
```

### 2. Configuration Updates
```python
# src/meetingmuse/config/config.py additions
class Config:
    # Existing config...

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")
    GOOGLE_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events"
    ]

    # Security Configuration
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    SESSION_ENCRYPTION_KEY: Optional[str] = os.getenv("SESSION_ENCRYPTION_KEY")
```

### 3. New Service Classes

#### 3.1 OAuth Service
```python
# src/meetingmuse/services/oauth_service.py
class OAuthService:
    """Handles Google OAuth 2.0 authentication flow"""

    async def get_authorization_url(self, client_id: str) -> str:
        """Generate OAuth authorization URL"""

    async def handle_callback(self, code: str, client_id: str) -> TokenInfo:
        """Process OAuth callback and exchange code for tokens"""

    async def refresh_token(self, refresh_token: str) -> TokenInfo:
        """Refresh access token using refresh token"""

    async def validate_token(self, access_token: str) -> bool:
        """Validate access token"""
```

#### 3.2 Google Calendar Service
```python
# src/meetingmuse/services/google_calendar_service.py
class GoogleCalendarService:
    """Handles Google Calendar API operations"""

    def __init__(self, credentials: Credentials):
        self.service = build('calendar', 'v3', credentials=credentials)

    async def list_events(self, calendar_id: str = 'primary') -> List[CalendarEvent]:
        """List calendar events"""

    async def create_event(self, event_data: MeetingFindings) -> CalendarEvent:
        """Create a new calendar event"""

    async def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if time slot is available"""
```

### 4. Database Schema (Future)
```sql
-- Session storage for OAuth tokens
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT ENCRYPTED,
    refresh_token TEXT ENCRYPTED,
    token_expiry TIMESTAMP,
    scopes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

---

## Security Considerations

### 1. Token Security
- **Encryption**: All tokens encrypted at rest using `cryptography` library
- **Secure Storage**: Server-side session storage with secure keys
- **Token Rotation**: Automatic refresh token rotation
- **Expiration Handling**: Graceful token expiration management

### 2. API Security
- **Rate Limiting**: Implement rate limits for OAuth and Calendar API calls
- **Input Validation**: Strict validation of all OAuth parameters
- **CORS Configuration**: Proper CORS setup for OAuth redirects
- **Error Handling**: Secure error messages without token exposure

### 3. WebSocket Security
- **Authenticated Connections**: Require valid tokens for WebSocket connections
- **Session Validation**: Continuous session validation during WebSocket lifetime
- **Message Encryption**: Consider message-level encryption for sensitive data

---

## API Endpoints

### 1. Authentication Endpoints
```python
# New auth API routes
GET  /auth/login/{client_id}           # Start OAuth flow
GET  /auth/callback                    # OAuth callback handler
POST /auth/refresh                     # Refresh token
POST /auth/logout/{client_id}          # Logout and revoke tokens
GET  /auth/status/{client_id}          # Check auth status
```

### 2. Calendar Endpoints
```python
# New calendar API routes
GET    /calendar/events/{client_id}              # List events
POST   /calendar/events/{client_id}              # Create event
GET    /calendar/availability/{client_id}        # Check availability
```

### 3. Enhanced WebSocket Protocol
```json
// Authentication message
{
  "type": "authenticate",
  "auth_token": "jwt_token_here",
  "timestamp": "2025-08-12T10:30:00Z"
}

// Calendar operation messages
{
  "type": "calendar_request",
  "operation": "create_event",
  "data": {
    "title": "Team Meeting",
    "start_time": "2025-08-13T14:00:00Z",
    "duration": "1 hour",
    "attendees": ["john@example.com"]
  }
}

// Calendar operation response
{
  "type": "calendar_response",
  "operation": "create_event",
  "success": true,
  "data": {
    "event_id": "google_event_id_123",
    "calendar_url": "https://calendar.google.com/event?eid=..."
  }
}
```

---

## Testing Strategy

### 1. Unit Tests
```python
# Test OAuth service
tests/meetingmuse/services/test_oauth_service.py
tests/meetingmuse/services/test_google_calendar_service.py

# Test calendar models
tests/meetingmuse/models/test_calendar_models.py

# Test auth API
tests/server/api/test_auth_api.py
```

### 2. Integration Tests
```python
# Test OAuth flow end-to-end
tests/integration/test_oauth_flow.py

# Test calendar operations
tests/integration/test_calendar_integration.py

# Test WebSocket with auth
tests/integration/test_authenticated_websocket.py
```

### 3. Manual Testing Scenarios
1. **OAuth Flow**: Complete authentication flow with Google
2. **Calendar Operations**: Create, read, update, delete events
3. **Token Refresh**: Verify automatic token refresh
4. **Error Scenarios**: Test network failures, invalid tokens, API limits
5. **WebSocket Integration**: Test real-time calendar operations through chat

---

## Deployment Considerations

### 1. Environment Configuration
```bash
# Production environment variables
GOOGLE_CLIENT_ID=your_production_client_id
GOOGLE_CLIENT_SECRET=your_production_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
JWT_SECRET_KEY=your_jwt_secret_256_bit_key
SESSION_ENCRYPTION_KEY=your_encryption_key_256_bit
```

### 2. Google Cloud Console Setup
1. **Create Project**: Set up Google Cloud project
2. **Enable APIs**: Enable Google Calendar API
3. **OAuth Consent**: Configure OAuth consent screen
4. **Credentials**: Create OAuth 2.0 client credentials
5. **Domain Verification**: Verify domain for production

### 3. Production Security
- **HTTPS Required**: All OAuth flows must use HTTPS in production
- **Domain Restrictions**: Restrict OAuth redirects to verified domains
- **Rate Limiting**: Implement comprehensive rate limiting
- **Monitoring**: Add OAuth and Calendar API monitoring

---

## Migration Strategy

### 1. Backward Compatibility
- **Graceful Degradation**: Continue simulated mode if OAuth not configured
- **Feature Flags**: Enable OAuth functionality with configuration flags
- **Legacy Support**: Maintain existing WebSocket protocol during transition

### 2. Rollout Plan
1. **Development Environment**: Full OAuth implementation and testing
2. **Staging Environment**: Complete integration testing with real Google Calendar
3. **Beta Release**: Limited user group with opt-in OAuth
4. **Production Release**: Full OAuth rollout with fallback to simulation

---

## Risk Assessment

### 1. Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Google API Rate Limits | Medium | High | Implement caching, rate limiting, and retry logic |
| OAuth Token Expiration | High | Medium | Automatic refresh token handling |
| Calendar API Changes | Low | High | Version pinning and API monitoring |
| WebSocket Auth Complexity | Medium | Medium | Thorough testing and fallback mechanisms |

### 2. Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User Privacy Concerns | Medium | Medium | Clear consent screens and minimal scope requests |
| OAuth Approval Delays | Low | High | Early submission to Google OAuth review |
| Calendar Integration Bugs | Medium | High | Comprehensive testing and gradual rollout |

---

## Success Criteria

### 1. Technical Success Metrics
- **OAuth Success Rate**: >95% successful authentication flows
- **Calendar API Success Rate**: >98% successful calendar operations
- **Response Time**: Calendar operations complete within 2 seconds
- **Token Refresh**: 100% successful automatic token refresh
- **Error Handling**: Graceful degradation for all failure scenarios

### 2. User Experience Metrics
- **Authentication Time**: Complete OAuth flow in <30 seconds
- **Calendar Sync**: Real calendar events visible in chat within 5 seconds
- **Meeting Creation**: New meetings appear in Google Calendar within 10 seconds
- **User Satisfaction**: >90% successful meeting scheduling attempts

### 3. Security Metrics
- **Token Security**: Zero token exposure incidents
- **API Security**: No unauthorized calendar access
- **Session Management**: Secure session handling with proper expiration

---

## Conclusion

This PRD provides a comprehensive roadmap for implementing Google OAuth 2.0 authentication and Google Calendar API integration in MeetingMuse. The implementation will transform the application from a simulated demo to a fully functional calendar management assistant, enabling real-world calendar operations while maintaining security and user experience standards.

The phased approach ensures minimal disruption to existing functionality while providing a clear path to full Google Calendar integration. Security considerations, testing strategies, and deployment guidelines ensure a robust and secure implementation.

**Next Steps**:
1. Review and approve this PRD
2. Set up Google Cloud project and OAuth credentials
3. Begin Phase 1 implementation with OAuth foundation
4. Establish testing framework for calendar integration
5. Plan rollout strategy for production deployment

---

*This document should be reviewed and updated as implementation progresses and requirements evolve.*

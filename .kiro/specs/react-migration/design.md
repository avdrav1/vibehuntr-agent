# Design Document: React + FastAPI Migration

## Overview

This design outlines the migration from Streamlit to a React + FastAPI architecture. The new architecture separates concerns cleanly: React handles UI state and rendering, FastAPI handles API requests and agent invocation, and ADK manages agent logic and conversation context.

**Key Benefits:**
- **No duplicate messages**: React's explicit state management prevents duplicates
- **Proper streaming**: SSE provides real-time token streaming without reruns
- **Production-ready**: Standard web architecture suitable for deployment
- **Better UX**: Responsive UI with fine-grained control over rendering
- **Maintainable**: Clear separation between frontend and backend

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  React Application (Port 5173)                         │ │
│  │  - Chat UI Components                                  │ │
│  │  - State Management (useState/useReducer)              │ │
│  │  - SSE Client for Streaming                            │ │
│  │  - Tailwind CSS Styling                                │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │ HTTP/SSE
                    │
┌───────────────────▼──────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer                                             │ │
│  │  - POST /api/chat (send message)                       │ │
│  │  - GET /api/chat/stream (SSE streaming)                │ │
│  │  - GET /api/sessions/{id}/messages                     │ │
│  │  - POST /api/sessions (create new)                     │ │
│  │  - DELETE /api/sessions/{id} (clear)                   │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Session Manager                                       │ │
│  │  - In-memory session storage                           │ │
│  │  - Message history per session                         │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Agent Invoker (Existing)                              │ │
│  │  - Reuse existing agent_invoker.py                     │ │
│  │  - Stream tokens from ADK                              │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │  ADK Agent           │
         │  (Existing)          │
         │  - Agent logic       │
         │  - Tools             │
         │  - Session service   │
         └─────────────────────┘
```

## Components and Interfaces

### 1. React Frontend

#### Directory Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat.tsx              # Main chat container
│   │   ├── MessageList.tsx       # Message display
│   │   ├── Message.tsx           # Individual message
│   │   ├── ChatInput.tsx         # Input field
│   │   └── Header.tsx            # App header
│   ├── hooks/
│   │   ├── useChat.ts            # Chat state management
│   │   └── useSSE.ts             # SSE streaming hook
│   ├── services/
│   │   └── api.ts                # API client
│   ├── types/
│   │   └── index.ts              # TypeScript types
│   ├── App.tsx                   # Root component
│   ├── main.tsx                  # Entry point
│   └── index.css                 # Tailwind imports
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

#### Key Components

**Chat.tsx** - Main container
```typescript
export function Chat() {
  const {
    messages,
    isStreaming,
    sendMessage,
    clearSession
  } = useChat();

  return (
    <div className="chat-container">
      <Header onClear={clearSession} />
      <MessageList messages={messages} isStreaming={isStreaming} />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
```

**useChat.ts** - State management hook
```typescript
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = async (content: string) => {
    // Add user message
    const userMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);

    // Start streaming
    setIsStreaming(true);
    const assistantMessage = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, assistantMessage]);

    // Stream response
    const eventSource = new EventSource(
      `/api/chat/stream?session_id=${sessionId}&message=${encodeURIComponent(content)}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'token') {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1].content += data.content;
          return updated;
        });
      } else if (data.type === 'done') {
        setIsStreaming(false);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };
  };

  return { messages, isStreaming, sendMessage, clearSession };
}
```

### 2. FastAPI Backend

#### Directory Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py               # Chat endpoints
│   │   └── sessions.py           # Session endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_manager.py    # Session management
│   │   └── agent_service.py      # Agent invocation wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Configuration
│   ├── main.py                   # FastAPI app
│   └── __init__.py
├── requirements.txt
└── README.md
```

#### API Endpoints

**POST /api/chat**
```python
@router.post("/chat")
async def send_message(request: ChatRequest):
    """Send a message and get complete response (non-streaming)."""
    session_manager.add_message(request.session_id, "user", request.message)
    
    response = await agent_service.invoke_agent(
        message=request.message,
        session_id=request.session_id
    )
    
    session_manager.add_message(request.session_id, "assistant", response)
    
    return {"response": response}
```

**GET /api/chat/stream**
```python
@router.get("/chat/stream")
async def stream_chat(session_id: str, message: str):
    """Stream agent response via Server-Sent Events."""
    
    async def event_generator():
        try:
            # Add user message
            session_manager.add_message(session_id, "user", message)
            
            # Stream agent response
            async for token in agent_service.stream_agent(message, session_id):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "token", "content": token})
                }
            
            # Send completion
            yield {
                "event": "message",
                "data": json.dumps({"type": "done"})
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "message": str(e)})
            }
    
    return EventSourceResponse(event_generator())
```

**GET /api/sessions/{session_id}/messages**
```python
@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    """Get all messages for a session."""
    messages = session_manager.get_messages(session_id)
    return {"messages": messages}
```

**POST /api/sessions**
```python
@router.post("/sessions")
async def create_session():
    """Create a new session."""
    session_id = str(uuid.uuid4())
    session_manager.create_session(session_id)
    return {"session_id": session_id}
```

**DELETE /api/sessions/{session_id}**
```python
@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a session's history."""
    session_manager.clear_session(session_id)
    return {"status": "cleared"}
```

### 3. Session Manager

```python
class SessionManager:
    """Manages conversation sessions and message history."""
    
    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}
    
    def create_session(self, session_id: str) -> None:
        """Create a new session."""
        self.sessions[session_id] = []
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str) -> None:
        """Clear a session's history."""
        if session_id in self.sessions:
            self.sessions[session_id] = []
```

### 4. Agent Service

```python
class AgentService:
    """Wrapper around existing agent_invoker for FastAPI integration."""
    
    def __init__(self):
        from app.event_planning.agent_loader import get_agent
        self.agent = get_agent()
    
    async def stream_agent(
        self,
        message: str,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream agent response tokens."""
        from app.event_planning.agent_invoker import invoke_agent_streaming
        
        for item in invoke_agent_streaming(
            self.agent,
            message,
            session_id=session_id,
            user_id="web_user",
            yield_tool_calls=False
        ):
            if item['type'] == 'text':
                yield item['content']
```

## Data Models

### TypeScript Types (Frontend)

```typescript
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatState {
  messages: Message[];
  sessionId: string;
  isStreaming: boolean;
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  response: string;
}

export interface SessionResponse {
  session_id: string;
}
```

### Python Models (Backend)

```python
from pydantic import BaseModel
from typing import Literal

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str | None = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class SessionResponse(BaseModel):
    session_id: str

class MessagesResponse(BaseModel):
    messages: list[Message]
```

## Error Handling

### Frontend Error Handling

```typescript
try {
  await sendMessage(content);
} catch (error) {
  setMessages(prev => [...prev, {
    role: 'assistant',
    content: `🚫 Error: ${error.message}`
  }]);
}
```

### Backend Error Handling

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}
    )
```

## Testing Strategy

### Frontend Tests (Vitest + React Testing Library)

```typescript
describe('Chat Component', () => {
  it('displays messages without duplicates', () => {
    const messages = [
      { role: 'user', content: 'Hello' },
      { role: 'assistant', content: 'Hi there!' }
    ];
    
    render(<MessageList messages={messages} />);
    
    expect(screen.getAllByText('Hello')).toHaveLength(1);
    expect(screen.getAllByText('Hi there!')).toHaveLength(1);
  });
  
  it('streams response tokens', async () => {
    // Test streaming updates
  });
});
```

### Backend Tests (pytest)

```python
def test_send_message(client):
    response = client.post("/api/chat", json={
        "session_id": "test-session",
        "message": "Hello"
    })
    
    assert response.status_code == 200
    assert "response" in response.json()

def test_stream_chat(client):
    # Test SSE streaming
    pass
```

## Deployment

### Development

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev  # Runs on port 5173
```

### Production

**Backend (Cloud Run)**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Frontend (Cloud Storage + CDN)**
```bash
npm run build
# Upload dist/ to Cloud Storage
# Configure CDN
```

## Migration Strategy

1. **Phase 1**: Set up FastAPI backend with basic endpoints
2. **Phase 2**: Create React frontend with basic chat UI
3. **Phase 3**: Implement SSE streaming
4. **Phase 4**: Add session management
5. **Phase 5**: Apply Vibehuntr branding
6. **Phase 6**: Add error handling and polish
7. **Phase 7**: Write tests
8. **Phase 8**: Deploy and verify

## Backward Compatibility

- Reuse `app/event_planning/agent_invoker.py`
- Reuse `app/event_planning/agent_loader.py`
- Reuse all agent tools and services
- Keep existing `.env` configuration
- Maintain ADK session service for agent context

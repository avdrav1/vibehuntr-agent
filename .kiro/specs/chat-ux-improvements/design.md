# Design Document: Chat UX Improvements

## Overview

This design document outlines the architecture and implementation approach for four key UX improvements to the Vibehuntr chat interface:

1. **Conversation History Sidebar** - A collapsible panel for browsing and switching between past sessions
2. **Typing Indicator** - Visual feedback while the agent processes requests
3. **Retry Individual Messages** - Recovery mechanism for failed messages
4. **Edit Sent Messages** - Ability to modify and re-send user messages

These features enhance the chat experience by providing better session management, clearer system feedback, and more flexible message handling.

## Architecture

The implementation follows the existing React component architecture with hooks for state management. New components will be added alongside existing ones, and the `useChat` hook will be extended to support new functionality.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 App Component                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌───────────────────────────────────┐ ┌────────────────────────┐ │
│ │  Session   │ │           Chat Area               │ │   Context Display      │ │
│ │  Sidebar   │ │ ┌───────────────────────────────┐ │ │   (Agent Memory)       │ │
│ │            │ │ │          Header                │ │ │                        │ │
│ │ ┌────────┐ │ │ └───────────────────────────────┘ │ │ ┌────────────────────┐ │ │
│ │ │Session │ │ │ ┌───────────────────────────────┐ │ │ │ Event Preferences  │ │ │
│ │ │ List   │ │ │ │       MessageList             │ │ │ │ User Info          │ │ │
│ │ │        │ │ │ │ ┌─────────────────────────┐   │ │ │ │ Group Info         │ │ │
│ │ │- Sess1 │ │ │ │ │ Message (edit/retry)   │   │ │ │ │ ...                │ │ │
│ │ │- Sess2 │ │ │ │ └─────────────────────────┘   │ │ │ └────────────────────┘ │ │
│ │ │- Sess3 │ │ │ │ ┌─────────────────────────┐   │ │ │                        │ │
│ │ └────────┘ │ │ │ │ TypingIndicator        │   │ │ │                        │ │
│ │            │ │ │ └─────────────────────────┘   │ │ │                        │ │
│ │[+ New Chat]│ │ └───────────────────────────────┘ │ │                        │ │
│ └────────────┘ │ ┌───────────────────────────────┐ │ │                        │ │
│                │ │         ChatInput             │ │ │                        │ │
│                │ └───────────────────────────────┘ │ │                        │ │
│                └───────────────────────────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

The layout maintains the existing ContextDisplay component (Agent Memory) on the right side while adding the new SessionSidebar on the left. The three-panel layout provides:
- **Left**: Session history sidebar for conversation management
- **Center**: Main chat interface with messages, typing indicator, and input
- **Right**: Agent memory/context display (existing functionality preserved)

## Components and Interfaces

### New Components

#### 1. SessionSidebar Component

```typescript
interface SessionSidebarProps {
  sessions: SessionSummary[];
  currentSessionId: string;
  isCollapsed: boolean;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete: (sessionId: string) => void;
  onNewSession: () => void;
  onToggleCollapse: () => void;
}

interface SessionSummary {
  id: string;
  preview: string;        // First message preview (truncated)
  timestamp: string;      // ISO timestamp of last activity
  messageCount: number;
}
```

#### 2. TypingIndicator Component

```typescript
interface TypingIndicatorProps {
  isVisible: boolean;
}
```

#### 3. Enhanced Message Component

```typescript
interface MessageProps {
  message: Message;
  isStreaming?: boolean;
  sessionId?: string;
  isFailed?: boolean;           // New: indicates failed message
  isEditing?: boolean;          // New: indicates edit mode
  onRetry?: () => void;         // New: retry callback
  onEdit?: () => void;          // New: enter edit mode
  onSaveEdit?: (content: string) => void;  // New: save edited message
  onCancelEdit?: () => void;    // New: cancel editing
}
```

### Extended Hooks

#### useChat Hook Extensions

```typescript
interface UseChatReturn {
  // Existing
  messages: Message[];
  sessionId: string;
  isStreaming: boolean;
  isLoading: boolean;
  // ...
  
  // New additions
  sessions: SessionSummary[];           // List of all sessions
  editingMessageIndex: number | null;   // Index of message being edited
  failedMessageIndices: Set<number>;    // Indices of failed messages
  
  // New methods
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  retryMessage: (messageIndex: number) => Promise<void>;
  startEditMessage: (messageIndex: number) => void;
  saveEditMessage: (messageIndex: number, newContent: string) => Promise<void>;
  cancelEditMessage: () => void;
}
```

### API Extensions

#### Backend Endpoints

```typescript
// GET /api/sessions - List all sessions for the user
interface SessionListResponse {
  sessions: SessionSummary[];
}

// DELETE /api/sessions/:sessionId - Delete a specific session
interface DeleteSessionResponse {
  success: boolean;
}
```

## Data Models

### SessionSummary

```typescript
interface SessionSummary {
  id: string;
  preview: string;      // First 100 chars of first message
  timestamp: string;    // ISO 8601 timestamp
  messageCount: number;
}
```

### Extended Message Type

```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  status?: 'sent' | 'failed' | 'pending';  // New: message status
  error?: string;                           // New: error message if failed
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: New sessions appear at list top
*For any* new session created, the session list should have that session at index 0 (top of the list)
**Validates: Requirements 1.3**

### Property 2: Session preview matches first message
*For any* session with at least one message, the session preview should contain a substring of the first message's content
**Validates: Requirements 1.4**

### Property 3: Deleted sessions are removed
*For any* session that is deleted, querying the session list should not include that session ID
**Validates: Requirements 1.6**

### Property 4: Typing indicator lifecycle
*For any* message send operation, the typing indicator should be visible while isLoading is true, and should be hidden once isStreaming becomes true or an error occurs
**Validates: Requirements 2.1, 2.3, 2.4**

### Property 5: Failed messages show retry
*For any* message with status 'failed', the retry button should be visible in the UI
**Validates: Requirements 3.1**

### Property 6: Retry sends same content
*For any* retry operation on a failed message, the content sent to the agent should equal the original message content
**Validates: Requirements 3.2**

### Property 7: Successful retry replaces response
*For any* successful retry, the message list should contain exactly one assistant response for that user message (the new one)
**Validates: Requirements 3.4**

### Property 8: Edit input contains original
*For any* message entering edit mode, the edit input field should contain the exact original message content
**Validates: Requirements 4.2**

### Property 9: Edit removes subsequent messages
*For any* saved edit at index N, all messages with index > N should be removed from the message list before re-sending
**Validates: Requirements 4.4**

### Property 10: Cancel preserves original
*For any* cancelled edit operation, the message content should equal the original content before editing began
**Validates: Requirements 4.5**

### Property 11: Edit mode disables input
*For any* active edit operation (editingMessageIndex !== null), the main chat input should be disabled
**Validates: Requirements 4.6**

## Error Handling

### Session Loading Errors
- If session data fails to load, display error toast and keep current session active
- Log error details for debugging

### Retry Errors
- If retry fails, update message status to 'failed' with new error
- Keep retry button visible for subsequent attempts
- Show user-friendly error message

### Edit Errors
- If edited message fails to send, treat as new failed message
- Allow retry of the edited content
- Do not restore deleted messages on failure

### Storage Errors
- If localStorage is unavailable, fall back to in-memory session list
- Warn user that history won't persist across page reloads

## Testing Strategy

### Unit Testing

Unit tests will cover:
- SessionSidebar rendering with various session counts
- TypingIndicator visibility states
- Message component edit/retry button visibility
- Session list sorting logic
- Message status transitions

### Property-Based Testing

Property-based tests will use the `fast-check` library to verify correctness properties:

- **Property 1**: Generate random sessions, verify newest is always first
- **Property 2**: Generate sessions with messages, verify preview substring match
- **Property 3**: Generate session lists, delete random session, verify removal
- **Property 4**: Simulate message send lifecycle, verify indicator states
- **Property 5**: Generate messages with various statuses, verify retry visibility
- **Property 6**: Generate retry operations, verify content equality
- **Property 7**: Simulate successful retries, verify single response
- **Property 8**: Generate edit operations, verify input content
- **Property 9**: Generate edit-save operations, verify message removal
- **Property 10**: Generate edit-cancel operations, verify content preservation
- **Property 11**: Generate edit states, verify input disabled state

Each property-based test will:
- Run a minimum of 100 iterations
- Be tagged with the format: `**Feature: chat-ux-improvements, Property {number}: {property_text}**`
- Reference the specific requirements being validated

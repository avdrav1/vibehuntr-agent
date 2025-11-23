/**
 * App Component
 * 
 * Root component that initializes the chat interface.
 * Uses the useChat hook to manage session initialization and state.
 * 
 * Requirements:
 * - 3.1: Session initialization on app load
 * - 3.4: Load existing messages if session exists
 * - 8.1: Display user-friendly error messages
 * - 8.2: Show errors in the chat interface
 * - 8.5: Allow user to retry
 */

import './App.css'
import { Chat } from './components/Chat'
import { ErrorMessage } from './components/ErrorMessage'
import { useChat } from './hooks/useChat'

function App() {
  // Initialize chat with session management (Requirements 3.1, 3.4)
  const {
    messages,
    sessionId,
    isStreaming,
    isLoading,
    isConnected,
    error,
    context,
    contextRefreshTrigger,
    sendMessage,
    clearSession,
    retryLastMessage,
    dismissError,
  } = useChat();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Display error banner with retry functionality (Requirements 8.1, 8.2, 8.5) */}
      {error && (
        <div 
          style={{
            padding: '1rem',
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <ErrorMessage
              message={error}
              onRetry={retryLastMessage}
              onDismiss={dismissError}
            />
          </div>
        </div>
      )}
      
      {/* Main chat interface */}
      <Chat
        messages={messages}
        sessionId={sessionId}
        isStreaming={isStreaming}
        isLoading={isLoading}
        isConnected={isConnected}
        context={context}
        contextRefreshTrigger={contextRefreshTrigger}
        onSendMessage={sendMessage}
        onNewConversation={clearSession}
      />
    </div>
  )
}

export default App

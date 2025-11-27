import { useState } from 'react';
import { Header } from './Header';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ContextDisplay } from './ContextDisplay';
import { SessionSidebar } from './SessionSidebar';
import type { Message, ConversationContext, SessionSummary } from '../types';

interface ChatProps {
  messages: Message[];
  isStreaming: boolean;
  isLoading: boolean;
  isConnected: boolean;
  sessionId: string;
  context: ConversationContext | null;
  contextRefreshTrigger?: number;
  failedMessageIndices?: Set<number>;
  editingMessageIndex?: number | null;
  sessions?: SessionSummary[];
  onSendMessage: (message: string) => void;
  onNewConversation: () => void;
  onContextUpdate?: () => void;
  onRetryMessage?: (messageIndex: number) => void;
  onEditMessage?: (messageIndex: number) => void;
  onSaveEditMessage?: (messageIndex: number, newContent: string) => void;
  onCancelEditMessage?: () => void;
  onSessionSelect?: (sessionId: string) => void;
  onSessionDelete?: (sessionId: string) => void;
}

/**
 * Chat container component that composes the main chat interface
 * Implements Requirements:
 * - 1.1: Display a collapsible sidebar showing past conversation sessions
 * - 1.2: React SPA with component-based architecture / Load and display messages from selected session
 * - 1.3: Render messages from React state without duplicates
 * - 1.5: Display delete button on hover
 * - 1.6: Remove session from list and delete data
 * - 7.5: Show loading states and connection status
 * - 11.1: Display context information in the UI
 */
export function Chat({
  messages,
  isStreaming,
  isLoading,
  isConnected,
  sessionId,
  context,
  contextRefreshTrigger,
  failedMessageIndices,
  editingMessageIndex,
  sessions = [],
  onSendMessage,
  onNewConversation,
  onContextUpdate,
  onRetryMessage,
  onEditMessage,
  onSaveEditMessage,
  onCancelEditMessage,
  onSessionSelect,
  onSessionDelete,
}: ChatProps) {
  // State for sidebar collapse (Requirement 1.1)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  return (
    <div 
      className="chat-container"
      style={{
        display: 'flex',
        flexDirection: 'row',
        height: '100vh',
        width: '100%',
        backgroundColor: 'var(--color-bg)',
      }}
    >
      {/* Session sidebar for conversation history (Requirement 1.1) */}
      <SessionSidebar
        sessions={sessions}
        currentSessionId={sessionId}
        isCollapsed={isSidebarCollapsed}
        onSessionSelect={onSessionSelect || (() => {})}
        onSessionDelete={onSessionDelete || (() => {})}
        onNewSession={onNewConversation}
        onToggleCollapse={handleToggleSidebar}
      />

      {/* Main chat area */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          minWidth: 0,
        }}
      >
        {/* Header with new conversation button and connection status */}
        <Header onNewConversation={onNewConversation} isConnected={isConnected} />

        {/* Message list with auto-scroll */}
        <MessageList 
          messages={messages} 
          isStreaming={isStreaming} 
          isLoading={isLoading} 
          sessionId={sessionId}
          failedMessageIndices={failedMessageIndices}
          editingMessageIndex={editingMessageIndex}
          onRetryMessage={onRetryMessage}
          onEditMessage={onEditMessage}
          onSaveEditMessage={onSaveEditMessage}
          onCancelEditMessage={onCancelEditMessage}
        />

        {/* Input area - disabled during streaming, loading, or editing (Requirement 4.6) */}
        <ChatInput 
          onSend={onSendMessage} 
          disabled={isStreaming || isLoading} 
          isLoading={isLoading}
          isEditingMessage={editingMessageIndex !== null}
        />
      </div>

      {/* Context sidebar showing agent memory */}
      <div
        style={{
          width: '320px',
          borderLeft: '1px solid rgba(139, 92, 246, 0.2)',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          overflowY: 'auto',
          flexShrink: 0,
        }}
      >
        <ContextDisplay 
          sessionId={sessionId}
          context={context}
          refreshTrigger={contextRefreshTrigger}
          onContextUpdate={onContextUpdate}
        />
      </div>
    </div>
  );
}

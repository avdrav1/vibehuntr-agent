import { Header } from './Header';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ContextDisplay } from './ContextDisplay';
import type { Message, ConversationContext } from '../types';

interface ChatProps {
  messages: Message[];
  isStreaming: boolean;
  isLoading: boolean;
  isConnected: boolean;
  sessionId: string;
  context: ConversationContext | null;
  contextRefreshTrigger?: number;
  onSendMessage: (message: string) => void;
  onNewConversation: () => void;
  onContextUpdate?: () => void;
}

/**
 * Chat container component that composes the main chat interface
 * Implements Requirements:
 * - 1.2: React SPA with component-based architecture
 * - 1.3: Render messages from React state without duplicates
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
  onSendMessage,
  onNewConversation,
  onContextUpdate,
}: ChatProps) {
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
        <MessageList messages={messages} isStreaming={isStreaming} isLoading={isLoading} sessionId={sessionId} />

        {/* Input area - disabled during streaming or loading */}
        <ChatInput onSend={onSendMessage} disabled={isStreaming || isLoading} isLoading={isLoading} />
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

import { useEffect, useRef } from 'react';
import { Message } from './Message';
import { Welcome } from './Welcome';
import { TypingIndicator } from './TypingIndicator';
import type { Message as MessageType } from '../types';

interface MessageListProps {
  messages: MessageType[];
  isStreaming?: boolean;
  isLoading?: boolean;
  sessionId?: string;
  failedMessageIndices?: Set<number>;
  editingMessageIndex?: number | null;
  onRetryMessage?: (messageIndex: number) => void;
  onEditMessage?: (messageIndex: number) => void;
  onSaveEditMessage?: (messageIndex: number, newContent: string) => void;
  onCancelEditMessage?: () => void;
}

/**
 * MessageList component displays all chat messages and handles auto-scrolling
 * Implements Requirements:
 * - 6.1: Display messages without duplicates
 * - 6.2: No duplicate message elements on re-render
 * - 6.5: Append new messages without duplicating existing ones
 * - 7.5: Show loading indicator while waiting for first token
 */
export function MessageList({ 
  messages, 
  isStreaming = false, 
  isLoading = false, 
  sessionId = 'default',
  failedMessageIndices = new Set(),
  editingMessageIndex = null,
  onRetryMessage,
  onEditMessage,
  onSaveEditMessage,
  onCancelEditMessage,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new messages arrive or content updates
   * Uses smooth scrolling for better UX
   */
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages, isStreaming, isLoading]); // Re-run when messages change or streaming/loading status changes

  // Show welcome screen when no messages (Requirements 9.1, 9.4)
  if (messages.length === 0) {
    return <Welcome />;
  }

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto p-6 space-y-6"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {/* Map over messages array - each message rendered exactly once */}
      {messages.map((message, index) => {
        // Show streaming indicator on the last assistant message when streaming
        const isLastMessage = index === messages.length - 1;
        const showStreamingIndicator = isStreaming && isLastMessage && message.role === 'assistant';
        
        // Check if this message has failed (Requirement 3.1)
        const isFailed = failedMessageIndices.has(index) || message.status === 'failed';
        
        // Check if this message is being edited (Requirement 4.2)
        const isEditing = editingMessageIndex === index;
        
        // Only allow editing user messages that haven't failed
        const canEdit = message.role === 'user' && !isFailed && !isStreaming && !isLoading;
        
        return (
          <Message 
            key={`${message.role}-${index}-${message.timestamp || ''}`}
            message={message}
            isStreaming={showStreamingIndicator}
            sessionId={sessionId}
            isFailed={isFailed}
            isEditing={isEditing}
            onRetry={isFailed && onRetryMessage ? () => onRetryMessage(index) : undefined}
            onEdit={canEdit && onEditMessage ? () => onEditMessage(index) : undefined}
            onSaveEdit={isEditing && onSaveEditMessage ? (content: string) => onSaveEditMessage(index, content) : undefined}
            onCancelEdit={isEditing ? onCancelEditMessage : undefined}
          />
        );
      })}
      
      {/* Typing indicator while waiting for first token (Requirements 2.1, 2.3, 2.4, 7.5)
          - Show when isLoading is true and not yet streaming
          - Hide when streaming starts (isStreaming becomes true) or error occurs */}
      <TypingIndicator isVisible={isLoading && !isStreaming} />
      
      {/* Invisible element at the end for auto-scroll target */}
      <div ref={messagesEndRef} />
    </div>
  );
}

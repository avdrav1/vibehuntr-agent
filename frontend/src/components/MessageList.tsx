import { useEffect, useRef } from 'react';
import { Message } from './Message';
import { Welcome } from './Welcome';
import type { Message as MessageType } from '../types';

interface MessageListProps {
  messages: MessageType[];
  isStreaming?: boolean;
  isLoading?: boolean;
}

/**
 * MessageList component displays all chat messages and handles auto-scrolling
 * Implements Requirements:
 * - 6.1: Display messages without duplicates
 * - 6.2: No duplicate message elements on re-render
 * - 6.5: Append new messages without duplicating existing ones
 * - 7.5: Show loading indicator while waiting for first token
 */
export function MessageList({ messages, isStreaming = false, isLoading = false }: MessageListProps) {
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
        
        return (
          <Message 
            key={`${message.role}-${index}-${message.timestamp || ''}`}
            message={message}
            isStreaming={showStreamingIndicator}
          />
        );
      })}
      
      {/* Loading indicator while waiting for first token (Requirement 7.5) */}
      {isLoading && (
        <div 
          className="flex items-center gap-3 p-4 glass fade-in"
          role="status"
          aria-live="polite"
          aria-label="Loading response"
        >
          <div className="text-lg" role="img" aria-label="Vibehuntr assistant">
            🎉
          </div>
          <div className="flex items-center gap-2">
            <div className="loading-dots">
              <span className="loading-dot"></span>
              <span className="loading-dot"></span>
              <span className="loading-dot"></span>
            </div>
            <span 
              className="text-sm"
              style={{ color: 'var(--color-text-muted)' }}
            >
              Thinking...
            </span>
          </div>
        </div>
      )}
      
      {/* Invisible element at the end for auto-scroll target */}
      <div ref={messagesEndRef} />
    </div>
  );
}

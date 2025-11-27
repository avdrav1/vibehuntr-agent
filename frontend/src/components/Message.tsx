import type { Message as MessageType } from '../types';
import { useMemo, useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { extractURLs } from '../utils/urlExtractor';
import { LinkPreview } from './LinkPreview';

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
  sessionId?: string;
  isFailed?: boolean;
  isEditing?: boolean;
  onRetry?: () => void;
  onEdit?: () => void;
  onSaveEdit?: (content: string) => void;
  onCancelEdit?: () => void;
}

interface VenueLink {
  name: string;
  url: string;
  placeId: string;
}

/**
 * Message component displays a single chat message with role-based styling
 * Implements Requirements:
 * - 6.1: Display messages without duplicates
 * - 9.2: Vibehuntr styling
 * - 7.3: Show visual indicator during streaming
 * - 7.4: Remove indicator when streaming completes
 * - 1.1: Extract URLs from message content
 * - 1.5: Display preview cards for all URLs in order
 * - 6.4: Exclude URLs already handled by venue links
 */
export function Message({ 
  message, 
  isStreaming = false, 
  sessionId = 'default', 
  isFailed = false, 
  isEditing = false,
  onRetry,
  onEdit,
  onSaveEdit,
  onCancelEdit,
}: MessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const editTextareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset edit content when entering edit mode (Requirement 4.2)
  useEffect(() => {
    if (isEditing) {
      setEditContent(message.content);
      // Focus the textarea when entering edit mode
      setTimeout(() => {
        editTextareaRef.current?.focus();
        // Move cursor to end
        if (editTextareaRef.current) {
          editTextareaRef.current.selectionStart = editTextareaRef.current.value.length;
          editTextareaRef.current.selectionEnd = editTextareaRef.current.value.length;
        }
      }, 0);
    }
  }, [isEditing, message.content]);

  // Handle save edit
  const handleSaveEdit = () => {
    if (editContent.trim() && onSaveEdit) {
      onSaveEdit(editContent.trim());
    }
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setEditContent(message.content);
    onCancelEdit?.();
  };

  // Handle keyboard shortcuts in edit mode
  const handleEditKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEdit();
    }
  };

  // Copy message content to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };
  
  /**
   * Extract venue information (name, website) from message content
   * Looks for patterns like:
   * - "🌐 Website: https://..."
   * And associates them with venue names
   * Place ID is optional - we'll use it if present for uniqueness, but not required
   */
  const venueLinks = useMemo((): VenueLink[] => {
    if (isUser || !message.content) return [];
    
    const links: VenueLink[] = [];
    const content = message.content;
    
    // Split by double newlines to get venue blocks
    const blocks = content.split('\n\n');
    
    for (const block of blocks) {
      // Look for venue name (usually starts with number or **name**)
      const nameMatch = block.match(/(?:\d+\.\s+)?\*\*([^*]+)\*\*/);
      // Look for website URL
      const websiteMatch = block.match(/🌐\s*Website:\s*(https?:\/\/[^\s\n]+)/i);
      // Look for Place ID (optional)
      const placeIdMatch = block.match(/(?:Place ID|🆔):\s*(ChI[a-zA-Z0-9_-]+)/i);
      
      // Only require name and website - Place ID is optional
      if (nameMatch && websiteMatch) {
        links.push({
          name: nameMatch[1].trim(),
          url: websiteMatch[1].trim(),
          placeId: placeIdMatch ? placeIdMatch[1].trim() : `link-${links.length}`,
        });
      }
    }
    
    return links;
  }, [message.content, isUser]);
  
  /**
   * Extract URLs for link previews (Requirements 1.1, 1.5, 6.4)
   * - Extract all valid HTTP/HTTPS URLs from message content
   * - Filter out URLs already handled by venue links to avoid duplication
   * - Maintain order of URLs as they appear in the message
   */
  const previewURLs = useMemo(() => {
    // Only extract URLs from assistant messages
    if (isUser || !message.content) return [];
    
    // Extract all valid URLs from message content
    const extractedURLs = extractURLs(message.content);
    
    // The extractURLs function already filters out venue link URLs
    // Return the URLs in the order they appear
    return extractedURLs.map(extracted => extracted.url);
  }, [message.content, isUser]);
  
  // Format timestamp to show actual time
  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return '';
      }
      
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      // Show just time for today's messages
      if (isToday) {
        return date.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
      }
      
      // Show date and time for older messages
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return '';
    }
  };

  const formattedTime = formatTimestamp(message.timestamp);

  return (
    <div
      className={`fade-in group ${isUser ? 'message-user' : 'message-assistant'}`}
      role="article"
      aria-label={`${isUser ? 'User' : 'Assistant'} message`}
    >
      {/* Role indicator */}
      <div className="flex items-center gap-2 mb-2">
        <div className="flex items-center gap-2">
          {isUser ? (
            <>
              <div className="text-lg" role="img" aria-label="User">
                👤
              </div>
              <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                You
              </span>
            </>
          ) : (
            <>
              <div className="text-lg" role="img" aria-label="Vibehuntr assistant">
                🎉
              </div>
              <span className="text-sm font-semibold text-gradient">
                Vibehuntr
              </span>
            </>
          )}
        </div>
        
        {/* Timestamp, edit button, and copy button */}
        <div className="flex items-center gap-2 ml-auto">
          {formattedTime && (
            <span 
              className="text-xs" 
              style={{ color: 'var(--color-text-muted)' }}
              aria-label={`Sent ${formattedTime}`}
            >
              {formattedTime}
            </span>
          )}
          
          {/* Edit button - only for user messages, not in edit mode (Requirement 4.1) */}
          {isUser && !isEditing && onEdit && (
            <button
              onClick={onEdit}
              className="p-1 rounded hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
              aria-label="Edit message"
              title="Edit message"
              data-testid="edit-button"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="14" 
                height="14" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                style={{ color: 'var(--color-text-muted)' }}
              >
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          )}
          
          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            aria-label={copied ? 'Copied!' : 'Copy message'}
            title={copied ? 'Copied!' : 'Copy message'}
          >
            {copied ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--color-primary)' }}>
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--color-text-muted)' }}>
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Message content */}
      <div 
        className="text-sm leading-relaxed break-words prose prose-invert prose-sm max-w-none"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {isUser && isEditing ? (
          // Edit mode: show textarea with save/cancel buttons (Requirements 4.2, 4.3)
          <div className="space-y-3">
            <textarea
              ref={editTextareaRef}
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onKeyDown={handleEditKeyDown}
              className="w-full p-3 rounded-lg resize-none overflow-hidden"
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid var(--color-primary)',
                color: 'var(--color-text-primary)',
                minHeight: '4rem',
              }}
              rows={3}
              aria-label="Edit message"
              data-testid="edit-textarea"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancelEdit}
                className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all hover:bg-white/10"
                style={{
                  border: '1px solid var(--color-text-muted)',
                  color: 'var(--color-text-secondary)',
                }}
                aria-label="Cancel edit"
                data-testid="cancel-edit-button"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={!editContent.trim()}
                className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all hover:scale-105"
                style={{
                  background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%)',
                  color: 'white',
                  opacity: editContent.trim() ? 1 : 0.5,
                  cursor: editContent.trim() ? 'pointer' : 'not-allowed',
                }}
                aria-label="Save edit"
                data-testid="save-edit-button"
              >
                Save & Resend
              </button>
            </div>
          </div>
        ) : isUser ? (
          // User messages rendered as plain text
          <span className="whitespace-pre-wrap">{message.content}</span>
        ) : (
          // Assistant messages rendered as markdown
          <ReactMarkdown
            components={{
              // Syntax highlighted code blocks
              code: ({ className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                const isInline = !match && !className;
                
                return isInline ? (
                  <code 
                    className="bg-white/10 px-1.5 py-0.5 rounded text-purple-300 text-xs"
                    {...props}
                  >
                    {children}
                  </code>
                ) : (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match ? match[1] : 'text'}
                    PreTag="div"
                    customStyle={{
                      margin: '0.5rem 0',
                      borderRadius: '0.5rem',
                      fontSize: '0.75rem',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                );
              },
              // Style links
              a: ({ href, children }) => (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300 underline"
                >
                  {children}
                </a>
              ),
              // Style lists
              ul: ({ children }) => (
                <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>
              ),
              // Style paragraphs
              p: ({ children }) => (
                <p className="my-2">{children}</p>
              ),
              // Style bold text
              strong: ({ children }) => (
                <strong className="font-semibold text-white">{children}</strong>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
        {/* Streaming cursor indicator (Requirements 7.3, 7.4) */}
        {isStreaming && message.role === 'assistant' && (
          <span 
            className="inline-block ml-1 w-2 h-4 cursor-blink"
            style={{ 
              background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%)'
            }}
            role="status"
            aria-label="Streaming in progress"
          />
        )}
      </div>
      
      {/* Venue website links - show when venues with websites are detected */}
      {venueLinks.length > 0 && (
        <div className="mt-4 space-y-2">
          {venueLinks.map((venue, index) => (
            <a
              key={`${venue.placeId}-${index}`}
              href={venue.url}
              target="_blank"
              rel="noopener noreferrer"
              className="venue-link-button"
              aria-label={`Visit ${venue.name} website`}
            >
              <span className="venue-link-icon">🌐</span>
              <span className="venue-link-text">Visit {venue.name}</span>
              <span className="venue-link-arrow">→</span>
            </a>
          ))}
        </div>
      )}
      
      {/* Link preview cards - show for URLs not handled by venue links (Requirements 1.1, 1.5, 6.4, 6.5) */}
      {previewURLs.length > 0 && import.meta.env.VITE_LINK_PREVIEW_ENABLED !== 'false' && (
        <div className="mt-4 space-y-3">
          {previewURLs.map((url, index) => (
            <LinkPreview
              key={`${url}-${index}`}
              url={url}
              sessionId={sessionId}
            />
          ))}
        </div>
      )}
      
      {/* Retry button for failed messages (Requirements 3.1, 3.4, 3.5) */}
      {(isFailed || message.status === 'failed') && isUser && onRetry && (
        <div className="mt-3 flex items-center gap-2">
          <span 
            className="text-xs"
            style={{ color: 'var(--color-error, #ef4444)' }}
          >
            {message.error || 'Failed to send'}
          </span>
          <button
            onClick={onRetry}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-all hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%)',
              color: 'white',
            }}
            aria-label="Retry sending message"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="12" 
              height="12" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M21 2v6h-6"></path>
              <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
              <path d="M3 22v-6h6"></path>
              <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
            </svg>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

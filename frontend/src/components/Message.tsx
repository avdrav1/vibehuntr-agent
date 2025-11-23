import type { Message as MessageType } from '../types';
import { useMemo } from 'react';

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
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
 */
export function Message({ message, isStreaming = false }: MessageProps) {
  const isUser = message.role === 'user';
  
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
  
  // Format timestamp if available
  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return '';
      }
      
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      // Show relative time for recent messages
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      
      // Show formatted date for older messages
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
      className={`fade-in ${isUser ? 'message-user' : 'message-assistant'}`}
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
        
        {/* Timestamp */}
        {formattedTime && (
          <span 
            className="text-xs ml-auto" 
            style={{ color: 'var(--color-text-muted)' }}
            aria-label={`Sent ${formattedTime}`}
          >
            {formattedTime}
          </span>
        )}
      </div>

      {/* Message content */}
      <div 
        className="text-sm leading-relaxed whitespace-pre-wrap break-words"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {message.content}
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
    </div>
  );
}

/**
 * ContextDisplay Component
 * 
 * Displays the current conversation context tracked by the agent.
 * Shows location, search query, and recent venues with ability to clear items.
 * 
 * Requirements: 11.1, 11.2, 11.4, 11.6, 11.7
 */

import { useState, useEffect } from 'react';
import type { ConversationContext } from '../types';
import { clearContext, clearContextItem } from '../services/api';

interface ContextDisplayProps {
  sessionId: string;
  context: ConversationContext | null;
  onContextUpdate?: () => void;
  refreshTrigger?: number; // Increment this to trigger a refresh
}

/**
 * ContextDisplay component shows the agent's memory of the conversation
 * Requirement 11.1: Visual indicator showing active context
 * Requirement 11.2: Display stored location, search query, and recent entities
 * Requirement 11.4: Update context display in real-time
 * Requirement 11.6: Ability to clear individual context items or all context
 * Requirement 11.7: Visual design consistent with Vibehuntr theme
 */
export function ContextDisplay({ sessionId, context, onContextUpdate, refreshTrigger }: ContextDisplayProps) {
  const [localContext, setLocalContext] = useState<ConversationContext | null>(context);
  const [error, setError] = useState<string | null>(null);

  // Update local context when prop changes
  useEffect(() => {
    setLocalContext(context);
  }, [context]);

  const handleClearAll = async () => {
    try {
      await clearContext(sessionId);
      setLocalContext({ recent_venues: [] });
      onContextUpdate?.();
    } catch (err) {
      console.error('Failed to clear context:', err);
      setError('Unable to clear agent memory');
    }
  };

  const handleClearItem = async (itemType: 'location' | 'query' | 'venue' | 'user_name' | 'user_email', index?: number) => {
    try {
      await clearContextItem(sessionId, itemType, index);
      
      // Update local state
      setLocalContext(prev => {
        if (!prev) return prev;
        
        const updated = { ...prev };
        if (itemType === 'location') {
          updated.location = undefined;
        } else if (itemType === 'query') {
          updated.search_query = undefined;
        } else if (itemType === 'user_name') {
          updated.user_name = undefined;
        } else if (itemType === 'user_email') {
          updated.user_email = undefined;
        } else if (itemType === 'venue' && index !== undefined) {
          updated.recent_venues = prev.recent_venues.filter((_, i) => i !== index);
        }
        return updated;
      });
      
      onContextUpdate?.();
    } catch (err) {
      console.error('Failed to clear context item:', err);
      setError('Unable to clear item');
    }
  };

  // Check if context has any data
  const hasContext = localContext && (
    localContext.user_name ||
    localContext.user_email ||
    localContext.location || 
    localContext.search_query ||
    localContext.event_venue_name ||
    localContext.event_date_time ||
    localContext.event_party_size ||
    localContext.recent_venues.length > 0
  );

  // Show placeholder when no context exists
  if (!hasContext) {
    return (
      <div
        style={{
          padding: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <span style={{ fontSize: '18px' }}>💭</span>
          <span style={{ fontSize: '14px', fontWeight: '600', color: '#9ca3af' }}>
            Agent Memory
          </span>
        </div>
        <div
          style={{
            backgroundColor: 'rgba(139, 92, 246, 0.05)',
            border: '2px dashed rgba(139, 92, 246, 0.3)',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center',
          }}
        >
          <p style={{ margin: '0', fontSize: '12px', color: '#6b7280', fontStyle: 'italic', lineHeight: '1.5' }}>
            I'll remember your name, email, location, and venue preferences as we chat
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '16px',
        color: '#e5e7eb',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>💭</span>
          <span style={{ fontWeight: '600', fontSize: '14px' }}>Agent Memory</span>
        </div>
        <button
          onClick={handleClearAll}
          style={{
            background: 'transparent',
            border: '1px solid rgba(139, 92, 246, 0.5)',
            borderRadius: '4px',
            padding: '3px 8px',
            color: '#e5e7eb',
            fontSize: '11px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(139, 92, 246, 0.2)';
            e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.8)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
          }}
        >
          Clear All
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div
          style={{
            color: '#ef4444',
            fontSize: '12px',
            marginBottom: '8px',
            padding: '4px 8px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '4px',
          }}
        >
          {error}
        </div>
      )}

      {/* Context items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* User Name */}
        {localContext?.user_name && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              padding: '10px',
              backgroundColor: 'rgba(139, 92, 246, 0.15)',
              borderRadius: '6px',
              border: '1px solid rgba(139, 92, 246, 0.3)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: '14px', flexShrink: 0 }}>👤</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Name</div>
                <div style={{ fontSize: '13px', fontWeight: '500', wordBreak: 'break-word' }}>{localContext.user_name}</div>
              </div>
            </div>
            <button
              onClick={() => handleClearItem('user_name')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '18px',
                padding: '0 4px',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#9ca3af';
              }}
              aria-label="Clear name"
            >
              ×
            </button>
          </div>
        )}

        {/* User Email */}
        {localContext?.user_email && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              padding: '10px',
              backgroundColor: 'rgba(139, 92, 246, 0.15)',
              borderRadius: '6px',
              border: '1px solid rgba(139, 92, 246, 0.3)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: '14px', flexShrink: 0 }}>📧</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Email</div>
                <div style={{ fontSize: '12px', fontWeight: '500', wordBreak: 'break-all' }}>{localContext.user_email}</div>
              </div>
            </div>
            <button
              onClick={() => handleClearItem('user_email')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '18px',
                padding: '0 4px',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#9ca3af';
              }}
              aria-label="Clear email"
            >
              ×
            </button>
          </div>
        )}

        {/* Event Planning Details */}
        {(localContext?.event_venue_name || localContext?.event_date_time || localContext?.event_party_size) && (
          <div
            style={{
              padding: '10px',
              backgroundColor: 'rgba(139, 92, 246, 0.15)',
              borderRadius: '6px',
              border: '1px solid rgba(139, 92, 246, 0.3)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px' }}>🎉</span>
              <div style={{ fontSize: '10px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Event Planning</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
              {localContext.event_venue_name && (
                <div>
                  <span style={{ color: '#9ca3af' }}>Venue:</span>{' '}
                  <span style={{ fontWeight: '500' }}>{localContext.event_venue_name}</span>
                </div>
              )}
              {localContext.event_party_size && (
                <div>
                  <span style={{ color: '#9ca3af' }}>Party size:</span>{' '}
                  <span style={{ fontWeight: '500' }}>{localContext.event_party_size} people</span>
                </div>
              )}
              {localContext.event_date_time && (
                <div>
                  <span style={{ color: '#9ca3af' }}>When:</span>{' '}
                  <span style={{ fontWeight: '500' }}>{localContext.event_date_time}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Location */}
        {localContext?.location && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: '14px', flexShrink: 0 }}>📍</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Location</div>
                <div style={{ fontSize: '13px', fontWeight: '500', wordBreak: 'break-word' }}>{localContext.location}</div>
              </div>
            </div>
            <button
              onClick={() => handleClearItem('location')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '0 4px',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#9ca3af';
              }}
              aria-label="Clear location"
            >
              ×
            </button>
          </div>
        )}

        {/* Search Query */}
        {localContext?.search_query && (
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: '14px', flexShrink: 0 }}>🔍</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Looking for</div>
                <div style={{ fontSize: '13px', fontWeight: '500', wordBreak: 'break-word' }}>{localContext.search_query}</div>
              </div>
            </div>
            <button
              onClick={() => handleClearItem('query')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '0 4px',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#9ca3af';
              }}
              aria-label="Clear search query"
            >
              ×
            </button>
          </div>
        )}

        {/* Recent Venues */}
        {localContext?.recent_venues && localContext.recent_venues.length > 0 && (
          <div
            style={{
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px' }}>🏪</span>
              <div style={{ fontSize: '10px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Recent Venues</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {localContext.recent_venues.map((venue, index) => (
                <div
                  key={`${venue.place_id}-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: '8px',
                  }}
                >
                  <span style={{ fontSize: '12px', flex: 1, minWidth: 0, wordBreak: 'break-word' }}>
                    • {venue.name}
                    {venue.location && (
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '11px', marginTop: '2px' }}>
                        {venue.location}
                      </span>
                    )}
                  </span>
                  <button
                    onClick={() => handleClearItem('venue', index)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#9ca3af',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: '0 4px',
                      transition: 'color 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = '#ef4444';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = '#9ca3af';
                    }}
                    aria-label={`Clear ${venue.name}`}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from 'react';
import type { SessionSummary } from '../types';

interface SessionSidebarProps {
  sessions: SessionSummary[];
  currentSessionId: string;
  isCollapsed: boolean;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete: (sessionId: string) => void;
  onNewSession: () => void;
  onToggleCollapse: () => void;
}

/**
 * SessionSidebar component for displaying and managing conversation history
 * Implements Requirements:
 * - 1.1: Display a collapsible sidebar showing past conversation sessions
 * - 1.2: Load and display messages from selected session
 * - 1.3: Add new session to top of conversation history
 * - 1.4: Show preview of first message and session timestamp
 * - 1.5: Display delete button on hover
 * - 1.6: Remove session from list and delete data
 */
export function SessionSidebar({
  sessions,
  currentSessionId,
  isCollapsed,
  onSessionSelect,
  onSessionDelete,
  onNewSession,
  onToggleCollapse,
}: SessionSidebarProps) {
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setDeleteConfirmId(sessionId);
  };

  const handleConfirmDelete = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    onSessionDelete(sessionId);
    setDeleteConfirmId(null);
  };


  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirmId(null);
  };

  // Collapsed state - show only toggle button
  if (isCollapsed) {
    return (
      <div
        className="session-sidebar-collapsed"
        style={{
          width: '48px',
          height: '100%',
          backgroundColor: 'rgba(26, 26, 46, 0.5)',
          borderRight: '1px solid rgba(255, 107, 107, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: '1rem',
        }}
      >
        <button
          onClick={onToggleCollapse}
          className="sidebar-toggle-btn"
          aria-label="Expand sidebar"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '0.375rem',
            backgroundColor: 'transparent',
            border: '1px solid rgba(255, 107, 107, 0.3)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div
      className="session-sidebar"
      style={{
        width: '280px',
        height: '100%',
        backgroundColor: 'rgba(26, 26, 46, 0.5)',
        borderRight: '1px solid rgba(255, 107, 107, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      {/* Header with collapse button */}
      <div
        style={{
          padding: '1rem',
          borderBottom: '1px solid rgba(255, 107, 107, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <h2
          style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            color: 'var(--color-text-secondary)',
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Conversations
        </h2>
        <button
          onClick={onToggleCollapse}
          className="sidebar-toggle-btn"
          aria-label="Collapse sidebar"
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '0.375rem',
            backgroundColor: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>


      {/* Session list */}
      <div
        className="custom-scrollbar"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.5rem',
        }}
      >
        {sessions.length === 0 ? (
          <div
            style={{
              padding: '2rem 1rem',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: '0.875rem',
            }}
          >
            No conversations yet
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onSessionSelect(session.id)}
              onMouseEnter={() => setHoveredSessionId(session.id)}
              onMouseLeave={() => {
                setHoveredSessionId(null);
                if (deleteConfirmId === session.id) {
                  setDeleteConfirmId(null);
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSessionSelect(session.id);
                }
              }}
              aria-selected={session.id === currentSessionId}
              style={{
                padding: '0.75rem',
                marginBottom: '0.25rem',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                backgroundColor:
                  session.id === currentSessionId
                    ? 'rgba(255, 107, 107, 0.15)'
                    : hoveredSessionId === session.id
                    ? 'rgba(255, 107, 107, 0.08)'
                    : 'transparent',
                border:
                  session.id === currentSessionId
                    ? '1px solid rgba(255, 107, 107, 0.3)'
                    : '1px solid transparent',
                transition: 'all 0.15s ease',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '0.5rem',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Session preview (Requirement 1.4) */}
                  <div
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'var(--color-text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      marginBottom: '0.25rem',
                    }}
                  >
                    {session.preview || 'New conversation'}
                  </div>
                  {/* Timestamp and message count (Requirement 1.4) */}
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    <span>{formatTimestamp(session.timestamp)}</span>
                    <span>•</span>
                    <span>
                      {session.messageCount} message{session.messageCount !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>


                {/* Delete button (Requirement 1.5) - shown on hover */}
                {hoveredSessionId === session.id && deleteConfirmId !== session.id && (
                  <button
                    onClick={(e) => handleDeleteClick(e, session.id)}
                    aria-label={`Delete conversation: ${session.preview || 'New conversation'}`}
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '0.25rem',
                      backgroundColor: 'transparent',
                      border: 'none',
                      color: 'var(--color-text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.15s',
                      flexShrink: 0,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = '#ef4444';
                      e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = 'var(--color-text-muted)';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
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
                    >
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                )}

                {/* Delete confirmation (Requirement 1.6) */}
                {deleteConfirmId === session.id && (
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.25rem',
                      flexShrink: 0,
                    }}
                  >
                    <button
                      onClick={(e) => handleConfirmDelete(e, session.id)}
                      aria-label="Confirm delete"
                      style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        backgroundColor: 'rgba(239, 68, 68, 0.2)',
                        border: '1px solid rgba(239, 68, 68, 0.4)',
                        color: '#fca5a5',
                        cursor: 'pointer',
                        fontSize: '0.625rem',
                        fontWeight: 500,
                        transition: 'all 0.15s',
                      }}
                    >
                      Delete
                    </button>
                    <button
                      onClick={handleCancelDelete}
                      aria-label="Cancel delete"
                      style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        backgroundColor: 'transparent',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        color: 'var(--color-text-muted)',
                        cursor: 'pointer',
                        fontSize: '0.625rem',
                        fontWeight: 500,
                        transition: 'all 0.15s',
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>


      {/* New session button (Requirement 1.3) */}
      <div
        style={{
          padding: '0.75rem',
          borderTop: '1px solid rgba(255, 107, 107, 0.2)',
        }}
      >
        <button
          onClick={onNewSession}
          className="btn-primary"
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1rem',
            fontSize: '0.875rem',
          }}
          aria-label="Start new conversation"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>New Chat</span>
        </button>
      </div>
    </div>
  );
}

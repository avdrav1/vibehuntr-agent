interface HeaderProps {
  onNewConversation: () => void;
  isConnected?: boolean;
}

/**
 * Header component with branding and connection status
 * Implements Requirements:
 * - 9.1: Vibehuntr branding
 * - 9.3: New conversation button
 * - 7.5: Show connection status
 */
export function Header({ onNewConversation, isConnected = true }: HeaderProps) {
  return (
    <header className="glass p-4 flex items-center justify-between">
      {/* Logo and Title */}
      <div className="flex items-center gap-3">
        <div className="text-3xl" role="img" aria-label="Vibehuntr logo">
          🎉
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gradient">
            Vibehuntr
          </h1>
          <div className="flex items-center gap-2">
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Discover. Plan. Vibe.
            </p>
            {/* Connection status indicator (Requirement 7.5) */}
            <div 
              className="flex items-center gap-1 text-xs"
              role="status"
              aria-live="polite"
              aria-label={isConnected ? 'Connected' : 'Disconnected'}
            >
              <div 
                className={`w-2 h-2 rounded-full ${isConnected ? 'connection-indicator-online' : 'connection-indicator-offline'}`}
                style={{
                  backgroundColor: isConnected ? '#4ade80' : '#ef4444',
                }}
              />
              <span style={{ color: isConnected ? '#4ade80' : '#ef4444' }}>
                {isConnected ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* New Conversation Button */}
      <button
        onClick={onNewConversation}
        className="btn-secondary flex items-center gap-2"
        aria-label="Start new conversation"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 5v14M5 12h14" />
        </svg>
        <span>New Conversation</span>
      </button>
    </header>
  );
}

/**
 * ErrorMessage Component
 * 
 * Displays error messages in the chat interface with retry functionality.
 * 
 * Requirements:
 * - 8.1: Display user-friendly error messages
 * - 8.2: Show errors in the chat interface
 * - 8.5: Allow user to retry
 */

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

/**
 * Error message component with retry and dismiss actions
 */
export function ErrorMessage({ message, onRetry, onDismiss }: ErrorMessageProps) {
  return (
    <div
      className="error-message"
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '0.75rem',
        padding: '1rem',
        margin: '0.5rem 0',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      {/* Error icon and message */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
        <span
          style={{
            fontSize: '1.25rem',
            flexShrink: 0,
          }}
          role="img"
          aria-label="error"
        >
          ⚠️
        </span>
        <div style={{ flex: 1 }}>
          <p
            style={{
              color: 'var(--color-text)',
              margin: 0,
              fontSize: '0.95rem',
              lineHeight: '1.5',
            }}
          >
            {message}
          </p>
        </div>
      </div>

      {/* Action buttons */}
      {(onRetry || onDismiss) && (
        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            justifyContent: 'flex-end',
          }}
        >
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="error-dismiss-button"
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backgroundColor: 'transparent',
                color: 'var(--color-text)',
                cursor: 'pointer',
                fontSize: '0.875rem',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              Dismiss
            </button>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="error-retry-button"
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                border: 'none',
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
                color: 'white',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(168, 85, 247, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              🔄 Retry
            </button>
          )}
        </div>
      )}
    </div>
  );
}

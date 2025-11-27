/**
 * TypingIndicator Component
 * 
 * Displays a visual indicator when the agent is processing a request.
 * Shows "Vibehuntr is thinking..." with animated dots.
 * 
 * Requirements:
 * - 2.1: Display typing indicator immediately when user sends a message
 * - 2.2: Show "Vibehuntr is thinking..." text with animated dots
 */

interface TypingIndicatorProps {
  /** Controls visibility of the typing indicator */
  isVisible: boolean;
}

/**
 * TypingIndicator displays animated feedback while the agent processes a request.
 * 
 * @param isVisible - When true, the indicator is shown; when false, it's hidden
 */
export function TypingIndicator({ isVisible }: TypingIndicatorProps) {
  if (!isVisible) {
    return null;
  }

  return (
    <div 
      className="flex items-center gap-3 p-4 glass fade-in"
      role="status"
      aria-live="polite"
      aria-label="Vibehuntr is thinking"
      data-testid="typing-indicator"
    >
      {/* Vibehuntr avatar */}
      <div className="text-lg" role="img" aria-label="Vibehuntr assistant">
        🎉
      </div>
      
      {/* Animated dots and text */}
      <div className="flex items-center gap-2">
        <div className="loading-dots" aria-hidden="true">
          <span className="loading-dot"></span>
          <span className="loading-dot"></span>
          <span className="loading-dot"></span>
        </div>
        <span 
          className="text-sm"
          style={{ color: 'var(--color-text-muted)' }}
        >
          Vibehuntr is thinking...
        </span>
      </div>
    </div>
  );
}

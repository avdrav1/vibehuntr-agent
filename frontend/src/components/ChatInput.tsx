import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  isEditingMessage?: boolean;
}

/**
 * ChatInput component provides a textarea for user input with send functionality
 * Implements Requirements:
 * - 1.4: React state management for input
 * - 7.5: Disable during streaming and loading
 * - 9.3: Vibehuntr button styling
 */
export function ChatInput({ onSend, disabled = false, isLoading = false, isEditingMessage = false }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus the input when component mounts
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Refocus when input becomes enabled after being disabled
  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  // Combined disabled state including edit mode (Requirement 4.6)
  const isDisabled = disabled || isEditingMessage;

  const handleSend = () => {
    const trimmedInput = input.trim();
    if (trimmedInput && !isDisabled) {
      onSend(trimmedInput);
      setInput('');
      
      // Reset textarea height and refocus
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        // Refocus the input after sending
        setTimeout(() => {
          textareaRef.current?.focus();
        }, 0);
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="glass p-4">
      <div className="flex gap-3 items-end">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          placeholder={
            isEditingMessage
              ? "Finish editing your message above..."
              : isLoading 
                ? "Loading response..." 
                : disabled 
                  ? "Waiting for response..." 
                  : "Type your message... (Shift+Enter for new line)"
          }
          className="input-field resize-none overflow-hidden"
          style={{
            minHeight: '2.5rem',
            maxHeight: '10rem',
          }}
          rows={1}
          aria-label="Message input"
          data-testid="chat-input"
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={isDisabled || !input.trim()}
          className="btn-primary flex items-center justify-center"
          style={{
            minWidth: '3rem',
            height: '2.5rem',
            opacity: isDisabled || !input.trim() ? 0.5 : 1,
            cursor: isDisabled || !input.trim() ? 'not-allowed' : 'pointer',
          }}
          aria-label="Send message"
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
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </div>

      {/* Helper text */}
      <div 
        className="text-xs mt-2" 
        style={{ color: 'var(--color-text-muted)' }}
      >
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
}

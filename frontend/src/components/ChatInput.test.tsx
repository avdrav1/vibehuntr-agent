import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from './ChatInput';

/**
 * Tests for ChatInput component
 * Requirements: 1.4, 7.5, 9.3
 */
describe('ChatInput Component', () => {
  describe('Basic Functionality (Requirement 1.4)', () => {
    it('renders textarea with correct placeholder', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('placeholder', 'Type your message... (Shift+Enter for new line)');
    });

    it('renders send button', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toBeInTheDocument();
    });

    it('updates input value when typing', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement;
      await user.type(textarea, 'Hello world');
      
      expect(textarea.value).toBe('Hello world');
    });

    it('calls onSend with trimmed message when send button clicked', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      const button = screen.getByLabelText('Send message');
      
      await user.type(textarea, '  Hello world  ');
      await user.click(button);
      
      expect(onSend).toHaveBeenCalledWith('Hello world');
    });

    it('clears input after sending message', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement;
      const button = screen.getByLabelText('Send message');
      
      await user.type(textarea, 'Test message');
      await user.click(button);
      
      expect(textarea.value).toBe('');
    });

    it('does not send empty messages', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const button = screen.getByLabelText('Send message');
      await user.click(button);
      
      expect(onSend).not.toHaveBeenCalled();
    });

    it('does not send whitespace-only messages', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      const button = screen.getByLabelText('Send message');
      
      await user.type(textarea, '   ');
      await user.click(button);
      
      expect(onSend).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('sends message on Enter key', async () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      
      await userEvent.type(textarea, 'Test message');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
      
      expect(onSend).toHaveBeenCalledWith('Test message');
    });

    it('does not send message on Shift+Enter', async () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      
      await userEvent.type(textarea, 'Line 1');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
      
      expect(onSend).not.toHaveBeenCalled();
    });

    it('clears input after Enter key send', async () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement;
      
      await userEvent.type(textarea, 'Test');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
      
      expect(textarea.value).toBe('');
    });

    it('shows helper text about keyboard shortcuts', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
    });
  });

  describe('Disabled State (Requirement 7.5)', () => {
    it('disables textarea when disabled prop is true', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toBeDisabled();
    });

    it('disables send button when disabled prop is true', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toBeDisabled();
    });

    it('disables send button when input is empty', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toBeDisabled();
    });

    it('enables send button when input has content', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      const button = screen.getByLabelText('Send message');
      
      await user.type(textarea, 'Test');
      
      expect(button).not.toBeDisabled();
    });

    it('does not call onSend when disabled', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} />);
      
      const button = screen.getByLabelText('Send message');
      await user.click(button);
      
      expect(onSend).not.toHaveBeenCalled();
    });

    it('shows loading placeholder when isLoading is true', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} isLoading={true} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toHaveAttribute('placeholder', 'Loading response...');
    });

    it('shows waiting placeholder when disabled but not loading', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} isLoading={false} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toHaveAttribute('placeholder', 'Waiting for response...');
    });
  });

  describe('Button Styling (Requirement 9.3)', () => {
    it('applies correct CSS classes to send button', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toHaveClass('btn-primary');
    });

    it('applies reduced opacity when button is disabled', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toHaveStyle({ opacity: '0.5' });
    });

    it('applies full opacity when button is enabled', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      await user.type(textarea, 'Test');
      
      const button = screen.getByLabelText('Send message');
      expect(button).toHaveStyle({ opacity: '1' });
    });

    it('applies not-allowed cursor when disabled', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} disabled={true} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button).toHaveStyle({ cursor: 'not-allowed' });
    });

    it('applies pointer cursor when enabled', async () => {
      const user = userEvent.setup();
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      await user.type(textarea, 'Test');
      
      const button = screen.getByLabelText('Send message');
      expect(button).toHaveStyle({ cursor: 'pointer' });
    });
  });

  describe('Textarea Auto-resize', () => {
    it('has correct initial styling', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toHaveClass('input-field', 'resize-none', 'overflow-hidden');
    });

    it('has correct min and max height constraints', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toHaveStyle({ minHeight: '2.5rem', maxHeight: '10rem' });
    });

    it('starts with single row', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea).toHaveAttribute('rows', '1');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      expect(screen.getByLabelText('Message input')).toBeInTheDocument();
      expect(screen.getByLabelText('Send message')).toBeInTheDocument();
    });

    it('textarea is keyboard accessible', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const textarea = screen.getByLabelText('Message input');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('button is keyboard accessible', () => {
      const onSend = vi.fn();
      render(<ChatInput onSend={onSend} />);
      
      const button = screen.getByLabelText('Send message');
      expect(button.tagName).toBe('BUTTON');
    });
  });
});

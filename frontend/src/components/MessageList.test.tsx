import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageList } from './MessageList';
import type { Message } from '../types';

/**
 * Tests for MessageList component
 * Requirements: 6.1, 6.2, 6.5, 7.5
 */
describe('MessageList Component', () => {
  describe('Message Display Without Duplicates (Requirements 6.1, 6.2)', () => {
    it('displays each message exactly once', () => {
      const messages: Message[] = [
        { role: 'user', content: 'First message' },
        { role: 'assistant', content: 'First response' },
        { role: 'user', content: 'Second message' },
      ];

      render(<MessageList messages={messages} />);
      
      // Each message should appear exactly once
      expect(screen.getAllByText('First message')).toHaveLength(1);
      expect(screen.getAllByText('First response')).toHaveLength(1);
      expect(screen.getAllByText('Second message')).toHaveLength(1);
    });

    it('does not create duplicate elements on re-render', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Test message' },
      ];

      const { rerender } = render(<MessageList messages={messages} />);
      
      // Re-render with same messages
      rerender(<MessageList messages={messages} />);
      
      // Should still only have one instance
      expect(screen.getAllByText('Test message')).toHaveLength(1);
    });

    it('appends new messages without duplicating existing ones', () => {
      const initialMessages: Message[] = [
        { role: 'user', content: 'Message 1' },
        { role: 'assistant', content: 'Response 1' },
      ];

      const { rerender } = render(<MessageList messages={initialMessages} />);
      
      // Add a new message
      const updatedMessages: Message[] = [
        ...initialMessages,
        { role: 'user', content: 'Message 2' },
      ];
      
      rerender(<MessageList messages={updatedMessages} />);
      
      // All messages should appear exactly once
      expect(screen.getAllByText('Message 1')).toHaveLength(1);
      expect(screen.getAllByText('Response 1')).toHaveLength(1);
      expect(screen.getAllByText('Message 2')).toHaveLength(1);
    });

    it('handles empty message list', () => {
      render(<MessageList messages={[]} />);
      
      // Should show welcome screen instead
      expect(screen.getByText(/Welcome to Vibehuntr/i)).toBeInTheDocument();
    });

    it('renders messages in correct order', () => {
      const messages: Message[] = [
        { role: 'user', content: 'First' },
        { role: 'assistant', content: 'Second' },
        { role: 'user', content: 'Third' },
      ];

      render(<MessageList messages={messages} />);
      
      const messageElements = screen.getAllByRole('article');
      expect(messageElements).toHaveLength(3);
      
      // Check order by checking text content
      expect(messageElements[0]).toHaveTextContent('First');
      expect(messageElements[1]).toHaveTextContent('Second');
      expect(messageElements[2]).toHaveTextContent('Third');
    });
  });

  describe('Streaming Indicator (Requirement 7.3)', () => {
    it('shows streaming indicator on last assistant message when streaming', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
        { role: 'assistant', content: 'Partial response...' },
      ];

      render(<MessageList messages={messages} isStreaming={true} />);
      
      expect(screen.getByLabelText('Streaming in progress')).toBeInTheDocument();
    });

    it('does not show streaming indicator when not streaming', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
        { role: 'assistant', content: 'Complete response' },
      ];

      render(<MessageList messages={messages} isStreaming={false} />);
      
      expect(screen.queryByLabelText('Streaming in progress')).not.toBeInTheDocument();
    });

    it('does not show streaming indicator on non-last messages', () => {
      const messages: Message[] = [
        { role: 'user', content: 'First question' },
        { role: 'assistant', content: 'First response' },
        { role: 'user', content: 'Second question' },
        { role: 'assistant', content: 'Streaming...' },
      ];

      render(<MessageList messages={messages} isStreaming={true} />);
      
      // Should only have one streaming indicator
      expect(screen.getAllByLabelText('Streaming in progress')).toHaveLength(1);
    });

    it('does not show streaming indicator if last message is from user', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
        { role: 'assistant', content: 'Response' },
        { role: 'user', content: 'Another question' },
      ];

      render(<MessageList messages={messages} isStreaming={true} />);
      
      expect(screen.queryByLabelText('Streaming in progress')).not.toBeInTheDocument();
    });
  });

  describe('Loading State (Requirement 7.5)', () => {
    it('shows loading indicator when isLoading is true', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
      ];

      render(<MessageList messages={messages} isLoading={true} />);
      
      expect(screen.getByLabelText('Loading response')).toBeInTheDocument();
      expect(screen.getByText('Thinking...')).toBeInTheDocument();
    });

    it('does not show loading indicator when isLoading is false', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
      ];

      render(<MessageList messages={messages} isLoading={false} />);
      
      expect(screen.queryByLabelText('Loading response')).not.toBeInTheDocument();
    });

    it('shows loading indicator with correct styling', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Question' },
      ];

      render(<MessageList messages={messages} isLoading={true} />);
      
      const loadingElement = screen.getByLabelText('Loading response');
      expect(loadingElement).toHaveClass('glass', 'fade-in');
    });
  });

  describe('Auto-scroll Behavior (Requirement 6.5)', () => {
    it('has scroll container with correct attributes', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Test' },
      ];

      render(<MessageList messages={messages} />);
      
      const container = screen.getByRole('log');
      expect(container).toHaveAttribute('aria-live', 'polite');
      expect(container).toHaveAttribute('aria-label', 'Chat messages');
    });

    it('includes scroll target element', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Test' },
      ];

      const { container } = render(<MessageList messages={messages} />);
      
      // The scroll target is an invisible div at the end
      const scrollContainer = container.querySelector('[role="log"]');
      expect(scrollContainer).toBeInTheDocument();
      expect(scrollContainer?.lastElementChild).toBeInTheDocument();
    });
  });

  describe('Welcome Screen', () => {
    it('shows welcome screen when no messages', () => {
      render(<MessageList messages={[]} />);
      
      expect(screen.getByText(/Welcome to Vibehuntr/i)).toBeInTheDocument();
    });

    it('does not show welcome screen when messages exist', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Hello' },
      ];

      render(<MessageList messages={messages} />);
      
      expect(screen.queryByText(/Welcome to Vibehuntr/i)).not.toBeInTheDocument();
    });
  });

  describe('Message Keys', () => {
    it('generates unique keys for messages', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Message 1', timestamp: '2024-01-01T10:00:00Z' },
        { role: 'assistant', content: 'Response 1', timestamp: '2024-01-01T10:00:01Z' },
        { role: 'user', content: 'Message 2', timestamp: '2024-01-01T10:00:02Z' },
      ];

      const { container } = render(<MessageList messages={messages} />);
      
      // All message elements should be rendered
      const messageElements = container.querySelectorAll('[role="article"]');
      expect(messageElements).toHaveLength(3);
    });

    it('handles messages without timestamps', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Message 1' },
        { role: 'assistant', content: 'Response 1' },
      ];

      const { container } = render(<MessageList messages={messages} />);
      
      const messageElements = container.querySelectorAll('[role="article"]');
      expect(messageElements).toHaveLength(2);
    });
  });
});

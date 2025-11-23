import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Message } from './Message';
import type { Message as MessageType } from '../types';

/**
 * Tests for Message component rendering
 * Requirements: 6.1, 9.2, 7.3, 7.4, 6.4
 */
describe('Message Component', () => {
  describe('Basic Rendering (Requirement 6.1)', () => {
    it('renders user message with correct content', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Hello, this is a test message',
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('Hello, this is a test message')).toBeInTheDocument();
      expect(screen.getByLabelText('User message')).toBeInTheDocument();
    });

    it('renders assistant message with correct content', () => {
      const message: MessageType = {
        role: 'assistant',
        content: 'This is an assistant response',
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('This is an assistant response')).toBeInTheDocument();
      expect(screen.getByLabelText('Assistant message')).toBeInTheDocument();
    });

    it('displays user role indicator', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Test',
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('You')).toBeInTheDocument();
      expect(screen.getByLabelText('User')).toBeInTheDocument();
    });

    it('displays assistant role indicator', () => {
      const message: MessageType = {
        role: 'assistant',
        content: 'Test',
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('Vibehuntr')).toBeInTheDocument();
      expect(screen.getByLabelText('Vibehuntr assistant')).toBeInTheDocument();
    });

    it('preserves whitespace and line breaks in content', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Line 1\nLine 2\n  Indented line',
      };

      render(<Message message={message} />);
      
      const contentElement = screen.getByText(/Line 1/);
      expect(contentElement).toHaveClass('whitespace-pre-wrap');
    });
  });

  describe('Streaming Indicator (Requirements 7.3, 7.4)', () => {
    it('shows streaming indicator for assistant message when streaming', () => {
      const message: MessageType = {
        role: 'assistant',
        content: 'Streaming response...',
      };

      render(<Message message={message} isStreaming={true} />);
      
      const indicator = screen.getByLabelText('Streaming in progress');
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveClass('cursor-blink');
    });

    it('does not show streaming indicator when not streaming', () => {
      const message: MessageType = {
        role: 'assistant',
        content: 'Complete response',
      };

      render(<Message message={message} isStreaming={false} />);
      
      expect(screen.queryByLabelText('Streaming in progress')).not.toBeInTheDocument();
    });

    it('does not show streaming indicator for user messages', () => {
      const message: MessageType = {
        role: 'user',
        content: 'User message',
      };

      render(<Message message={message} isStreaming={true} />);
      
      expect(screen.queryByLabelText('Streaming in progress')).not.toBeInTheDocument();
    });
  });

  describe('Timestamps (Requirement 6.4)', () => {
    it('displays "Just now" for very recent messages', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Hello',
        timestamp: new Date().toISOString(),
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });

    it('displays relative time for messages from minutes ago', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      const message: MessageType = {
        role: 'assistant',
        content: 'Response',
        timestamp: fiveMinutesAgo.toISOString(),
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });

    it('displays relative time for messages from hours ago', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
      const message: MessageType = {
        role: 'user',
        content: 'Question',
        timestamp: twoHoursAgo.toISOString(),
      };

      render(<Message message={message} />);
      
      expect(screen.getByText('2h ago')).toBeInTheDocument();
    });

    it('displays formatted date for messages from days ago', () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
      const message: MessageType = {
        role: 'assistant',
        content: 'Old response',
        timestamp: twoDaysAgo.toISOString(),
      };

      render(<Message message={message} />);
      
      // Should show formatted date like "Nov 19, 3:45 PM"
      const timestampElement = screen.getByLabelText(/Sent/);
      expect(timestampElement).toBeInTheDocument();
      expect(timestampElement.textContent).toMatch(/\w+ \d+, \d+:\d+ (AM|PM)/);
    });

    it('does not display timestamp when not provided', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Message without timestamp',
      };

      render(<Message message={message} />);
      
      // Should not have any timestamp element
      expect(screen.queryByLabelText(/Sent/)).not.toBeInTheDocument();
    });

    it('handles invalid timestamp gracefully', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Message with invalid timestamp',
        timestamp: 'invalid-date',
      };

      render(<Message message={message} />);
      
      // Should not crash and should not display timestamp
      expect(screen.queryByLabelText(/Sent/)).not.toBeInTheDocument();
    });
  });

  describe('Styling (Requirement 9.2)', () => {
    it('applies correct CSS classes to user messages', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Test',
      };

      render(<Message message={message} />);
      
      const messageElement = screen.getByLabelText('User message');
      expect(messageElement).toHaveClass('message-user');
    });

    it('applies correct CSS classes to assistant messages', () => {
      const message: MessageType = {
        role: 'assistant',
        content: 'Test',
      };

      render(<Message message={message} />);
      
      const messageElement = screen.getByLabelText('Assistant message');
      expect(messageElement).toHaveClass('message-assistant');
    });

    it('applies fade-in animation class', () => {
      const message: MessageType = {
        role: 'user',
        content: 'Test',
      };

      render(<Message message={message} />);
      
      const messageElement = screen.getByLabelText('User message');
      expect(messageElement).toHaveClass('fade-in');
    });
  });
});

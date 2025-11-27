/**
 * Property-based tests for TypingIndicator lifecycle
 * Tests universal properties that should hold across all inputs
 * 
 * **Feature: chat-ux-improvements, Property 4: Typing indicator lifecycle**
 * Uses fast-check for property-based testing
 * 
 * **Validates: Requirements 2.1, 2.3, 2.4**
 */

import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import fc from 'fast-check';
import { TypingIndicator } from './TypingIndicator';

// Ensure cleanup after each test iteration
afterEach(() => {
  cleanup();
});

describe('TypingIndicator - Property-Based Tests', () => {
  /**
   * Property 4: Typing indicator lifecycle
   * *For any* message send operation, the typing indicator should be visible 
   * while isLoading is true, and should be hidden once isStreaming becomes true 
   * or an error occurs
   * 
   * The component receives `isVisible` which is computed from the chat state:
   * - isVisible = isLoading && !isStreaming
   * - When an error occurs, isLoading is set to false, so isVisible becomes false
   * 
   * **Validates: Requirements 2.1, 2.3, 2.4**
   */
  describe('Property 4: Typing indicator lifecycle', () => {
    it('should be visible when isVisible=true and hidden when isVisible=false', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.boolean(), // isVisible
          (isVisible) => {
            cleanup(); // Clean up before each iteration
            
            const { container } = render(<TypingIndicator isVisible={isVisible} />);
            const indicator = container.querySelector('[data-testid="typing-indicator"]');
            
            if (isVisible) {
              expect(indicator).toBeInTheDocument();
            } else {
              expect(indicator).not.toBeInTheDocument();
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should display "Vibehuntr is thinking..." text when visible', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant(true), // Always test with visible=true for this property
          () => {
            cleanup(); // Clean up before each iteration
            
            render(<TypingIndicator isVisible={true} />);
            
            // Requirement 2.2: Show "Vibehuntr is thinking..." text
            expect(screen.getByText('Vibehuntr is thinking...')).toBeInTheDocument();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should have proper accessibility attributes when visible', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant(true),
          () => {
            cleanup(); // Clean up before each iteration
            
            render(<TypingIndicator isVisible={true} />);
            
            const indicator = screen.getByRole('status');
            
            // Should have proper ARIA attributes
            expect(indicator).toHaveAttribute('aria-live', 'polite');
            expect(indicator).toHaveAttribute('aria-label', 'Vibehuntr is thinking');
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should render nothing when not visible', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant(false),
          () => {
            cleanup(); // Clean up before each iteration
            
            const { container } = render(<TypingIndicator isVisible={false} />);
            
            // Should render nothing
            expect(container.firstChild).toBeNull();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should contain animated loading dots when visible', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant(true),
          () => {
            cleanup(); // Clean up before each iteration
            
            const { container } = render(<TypingIndicator isVisible={true} />);
            
            // Should have loading dots container
            const dotsContainer = container.querySelector('.loading-dots');
            expect(dotsContainer).toBeInTheDocument();
            
            // Should have exactly 3 dots
            const dots = container.querySelectorAll('.loading-dot');
            expect(dots.length).toBe(3);
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Test the state transition logic that determines indicator visibility
   * This tests the integration between useChat state and TypingIndicator
   */
  describe('State transition properties', () => {
    it('should transition from hidden to visible when loading starts', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant({ before: false, after: true }), // isVisible transition
          (transition) => {
            cleanup(); // Clean up before each iteration
            
            // Before: not visible
            const { rerender, container } = render(
              <TypingIndicator isVisible={transition.before} />
            );
            expect(container.querySelector('[data-testid="typing-indicator"]')).not.toBeInTheDocument();
            
            // After: visible
            rerender(<TypingIndicator isVisible={transition.after} />);
            expect(container.querySelector('[data-testid="typing-indicator"]')).toBeInTheDocument();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should transition from visible to hidden when streaming starts', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.constant({ before: true, after: false }), // visibility transition
          (transition) => {
            cleanup(); // Clean up before each iteration
            
            // Before: visible
            const { rerender, container } = render(
              <TypingIndicator isVisible={transition.before} />
            );
            expect(container.querySelector('[data-testid="typing-indicator"]')).toBeInTheDocument();
            
            // After: hidden (streaming started)
            rerender(<TypingIndicator isVisible={transition.after} />);
            expect(container.querySelector('[data-testid="typing-indicator"]')).not.toBeInTheDocument();
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    /**
     * Test that the visibility logic correctly handles all state combinations
     * This simulates the actual state machine in useChat:
     * - isLoading=true, isStreaming=false -> visible (waiting for first token)
     * - isLoading=false, isStreaming=true -> hidden (streaming in progress)
     * - isLoading=false, isStreaming=false -> hidden (idle or error)
     */
    it('should correctly compute visibility from isLoading and isStreaming states', { timeout: 10000 }, () => {
      fc.assert(
        fc.property(
          fc.boolean(), // isLoading
          fc.boolean(), // isStreaming
          (isLoading, isStreaming) => {
            cleanup(); // Clean up before each iteration
            
            // The visibility formula used in MessageList
            const isVisible = isLoading && !isStreaming;
            
            const { container } = render(<TypingIndicator isVisible={isVisible} />);
            const indicator = container.querySelector('[data-testid="typing-indicator"]');
            
            // Verify the expected behavior based on state
            if (isLoading && !isStreaming) {
              // Requirement 2.1, 2.3: Show when loading and not streaming
              expect(indicator).toBeInTheDocument();
            } else {
              // Requirement 2.4: Hide when streaming starts or not loading
              expect(indicator).not.toBeInTheDocument();
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

/**
 * Tests for ContextDisplay component
 * Requirements: 11.2, 11.4, 11.6
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContextDisplay } from './ContextDisplay';
import * as api from '../services/api';
import type { ContextResponse } from '../types';

// Mock the API module
vi.mock('../services/api', () => ({
  fetchContext: vi.fn(),
  clearContext: vi.fn(),
  clearContextItem: vi.fn(),
}));

describe('ContextDisplay Component', () => {
  const mockSessionId = 'test-session-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering with context (Requirement 11.2)', () => {
    it('renders location when present', async () => {
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });
    });

    it('renders search query when present', async () => {
      const mockContext: ContextResponse = {
        search_query: 'Indian food',
        recent_venues: [],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Indian food/)).toBeInTheDocument();
      });
    });

    it('renders recent venues when present', async () => {
      const mockContext: ContextResponse = {
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123', location: 'Philadelphia' },
          { name: 'Vedge', place_id: 'ChIJdef456' },
        ],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
        expect(screen.getByText(/Osteria/)).toBeInTheDocument();
        expect(screen.getByText(/Vedge/)).toBeInTheDocument();
        expect(screen.getByText(/\(Philadelphia\)/)).toBeInTheDocument();
      });
    });

    it('renders all context items together', async () => {
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian restaurants',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
        ],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Italian restaurants/)).toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
        expect(screen.getByText(/Osteria/)).toBeInTheDocument();
      });
    });

    it('displays Agent Memory header', async () => {
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText('Agent Memory')).toBeInTheDocument();
      });
    });

    it('displays Clear All button', async () => {
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Clear All/i })).toBeInTheDocument();
      });
    });
  });

  describe('Empty state (Requirement 11.2)', () => {
    it('does not render when context is empty', async () => {
      const mockContext: ContextResponse = {
        recent_venues: [],
      };

      const { container } = render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      expect(container.firstChild).toBeNull();
    });

    it('does not render when all context fields are undefined', async () => {
      const mockContext: ContextResponse = {
        location: undefined,
        search_query: undefined,
        recent_venues: [],
      };

      const { container } = render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Clear functionality (Requirement 11.6)', () => {
    it('calls clearContext API when Clear All is clicked', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      vi.mocked(api.clearContext).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      const clearAllButton = screen.getByRole('button', { name: /Clear All/i });
      await user.click(clearAllButton);

      expect(api.clearContext).toHaveBeenCalledWith(mockSessionId);
    });

    it('calls clearContextItem API when location clear button is clicked', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      const clearButton = screen.getByLabelText('Clear location');
      await user.click(clearButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'location', undefined);
    });

    it('calls clearContextItem API when search query clear button is clicked', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        search_query: 'Italian food',
        recent_venues: [],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
      });

      const clearButton = screen.getByLabelText('Clear search query');
      await user.click(clearButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'query', undefined);
    });

    it('calls clearContextItem API when venue clear button is clicked', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
          { name: 'Vedge', place_id: 'ChIJdef456' },
        ],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Osteria/)).toBeInTheDocument();
      });

      const clearButton = screen.getByLabelText('Clear Osteria');
      await user.click(clearButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'venue', 0);
    });

    it('updates local state after clearing location', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      const clearButton = screen.getByLabelText('Clear location');
      await user.click(clearButton);

      await waitFor(() => {
        expect(screen.queryByText(/Location:/)).not.toBeInTheDocument();
        // Search query should still be visible
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
      });
    });

    it('calls onContextUpdate callback after clearing', async () => {
      const user = userEvent.setup();
      const onContextUpdate = vi.fn();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      vi.mocked(api.clearContext).mockResolvedValue();

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} onContextUpdate={onContextUpdate} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      const clearAllButton = screen.getByRole('button', { name: /Clear All/i });
      await user.click(clearAllButton);

      await waitFor(() => {
        expect(onContextUpdate).toHaveBeenCalled();
      });
    });
  });

  describe('Real-time updates (Requirement 11.4)', () => {
    it('updates display when context prop changes', async () => {
      const mockContext1: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      const mockContext2: ContextResponse = {
        location: 'New York',
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={mockContext1} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });

      // Update context prop
      rerender(<ContextDisplay sessionId={mockSessionId} context={mockContext2} refreshTrigger={1} />);

      await waitFor(() => {
        expect(screen.getByText(/New York/)).toBeInTheDocument();
      });
    });

    it('updates display when context changes for different session', async () => {
      const mockContext1: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      const mockContext2: ContextResponse = {
        location: 'Boston',
        recent_venues: [],
      };

      const { rerender } = render(<ContextDisplay sessionId="session-1" context={mockContext1} />);

      await waitFor(() => {
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });

      // Change session and context
      rerender(<ContextDisplay sessionId="session-2" context={mockContext2} />);

      await waitFor(() => {
        expect(screen.getByText(/Boston/)).toBeInTheDocument();
      });
    });
  });

  describe('Error handling', () => {
    it('handles null context gracefully without crashing', async () => {
      const { container } = render(<ContextDisplay sessionId={mockSessionId} context={null} />);

      // Component should not crash and should not render anything when context is null
      expect(container.firstChild).toBeNull();
    });

    it('displays error message when clear fails', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      vi.mocked(api.clearContext).mockRejectedValue(new Error('Network error'));

      render(<ContextDisplay sessionId={mockSessionId} context={mockContext} />);

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      const clearAllButton = screen.getByRole('button', { name: /Clear All/i });
      await user.click(clearAllButton);

      await waitFor(() => {
        expect(screen.getByText(/Unable to clear agent memory/)).toBeInTheDocument();
      });
    });
  });
});

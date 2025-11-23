/**
 * Integration tests for ContextDisplay component with real-time updates
 * 
 * These tests verify the end-to-end behavior of context display including:
 * - Real-time updates during conversation
 * - Clear functionality integration
 * - Multi-turn context accumulation in UI
 * 
 * Requirements tested:
 * - 11.4: Real-time context updates
 * - 11.6: Clear functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContextDisplay } from '../components/ContextDisplay';
import * as api from '../services/api';
import type { ContextResponse } from '../types';

// Mock the API module
vi.mock('../services/api', () => ({
  fetchContext: vi.fn(),
  clearContext: vi.fn(),
  clearContextItem: vi.fn(),
}));

describe('ContextDisplay Integration Tests', () => {
  const mockSessionId = 'integration-test-session';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Real-time context updates during conversation (Requirement 11.4)', () => {
    it('updates display when location is added during conversation', async () => {
      // Initial state: no context
      const initialContext: ContextResponse = {
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={initialContext} refreshTrigger={0} />
      );

      // Initially, nothing should be displayed
      expect(screen.queryByText(/Agent Memory/)).not.toBeInTheDocument();

      // Simulate user sending message with location
      const updatedContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext} refreshTrigger={1} />
      );

      // Context display should now show location
      await waitFor(() => {
        expect(screen.getByText('Agent Memory')).toBeInTheDocument();
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });
    });

    it('updates display when search query is added during conversation', async () => {
      // Initial state: only location
      const initialContext: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={initialContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      // Simulate user sending message with search query
      const updatedContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext} refreshTrigger={1} />
      );

      // Context display should now show both location and search query
      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Italian food/)).toBeInTheDocument();
      });
    });

    it('updates display when venues are added from agent response', async () => {
      // Initial state: location and search query
      const initialContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={initialContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
      });

      // Simulate agent responding with venues
      const updatedContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123', location: 'Philadelphia' },
          { name: 'Vedge', place_id: 'ChIJdef456', location: 'Philadelphia' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext} refreshTrigger={1} />
      );

      // Context display should now show venues
      await waitFor(() => {
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
        expect(screen.getByText(/Osteria/)).toBeInTheDocument();
        expect(screen.getByText(/Vedge/)).toBeInTheDocument();
      });
    });

    it('accumulates context across multiple conversation turns', async () => {
      // Turn 1: User mentions location
      const context1: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={context1} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });

      // Turn 2: User adds search query
      const context2: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'sushi',
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={context2} refreshTrigger={1} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/sushi/)).toBeInTheDocument();
      });

      // Turn 3: Agent responds with venues
      const context3: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'sushi',
        recent_venues: [
          { name: 'Morimoto', place_id: 'ChIJsushi1' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={context3} refreshTrigger={2} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
        expect(screen.getByText(/Morimoto/)).toBeInTheDocument();
      });

      // Turn 4: More venues added
      const context4: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'sushi',
        recent_venues: [
          { name: 'Morimoto', place_id: 'ChIJsushi1' },
          { name: 'Zama', place_id: 'ChIJsushi2' },
          { name: 'Vic Sushi Bar', place_id: 'ChIJsushi3' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={context4} refreshTrigger={3} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Morimoto/)).toBeInTheDocument();
        expect(screen.getByText(/Zama/)).toBeInTheDocument();
        expect(screen.getByText(/Vic Sushi Bar/)).toBeInTheDocument();
      });
    });

    it('updates display when location changes', async () => {
      // Initial state: Philadelphia
      const initialContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={initialContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
      });

      // User changes location to New York
      const updatedContext: ContextResponse = {
        location: 'New York',
        search_query: 'Italian food',
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext} refreshTrigger={1} />
      );

      // Display should update to show new location
      await waitFor(() => {
        expect(screen.queryByText(/Philadelphia/)).not.toBeInTheDocument();
        expect(screen.getByText(/New York/)).toBeInTheDocument();
      });
    });

    it('handles venue list size limit (max 5 venues)', async () => {
      // Add 7 venues, should only show last 5
      const contextWithManyVenues: ContextResponse = {
        location: 'Philadelphia',
        recent_venues: [
          { name: 'Venue 1', place_id: 'ChIJ1' },
          { name: 'Venue 2', place_id: 'ChIJ2' },
          { name: 'Venue 3', place_id: 'ChIJ3' },
          { name: 'Venue 4', place_id: 'ChIJ4' },
          { name: 'Venue 5', place_id: 'ChIJ5' },
        ],
      };

      render(
        <ContextDisplay sessionId={mockSessionId} context={contextWithManyVenues} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
      });

      // Should show all 5 venues
      expect(screen.getByText(/Venue 1/)).toBeInTheDocument();
      expect(screen.getByText(/Venue 2/)).toBeInTheDocument();
      expect(screen.getByText(/Venue 3/)).toBeInTheDocument();
      expect(screen.getByText(/Venue 4/)).toBeInTheDocument();
      expect(screen.getByText(/Venue 5/)).toBeInTheDocument();
    });
  });

  describe('Clear functionality integration (Requirement 11.6)', () => {
    it('clears individual context items and updates display', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
        ],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={mockContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
      });

      // Clear location
      const clearLocationButton = screen.getByLabelText('Clear location');
      await user.click(clearLocationButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'location', undefined);

      // Simulate context update after clearing location
      const updatedContext1: ContextResponse = {
        search_query: 'Italian food',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext1} refreshTrigger={1} />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Location:/)).not.toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
      });

      // Clear search query
      const clearQueryButton = screen.getByLabelText('Clear search query');
      await user.click(clearQueryButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'query', undefined);

      // Simulate context update after clearing query
      const updatedContext2: ContextResponse = {
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext2} refreshTrigger={2} />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Location:/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Looking for:/)).not.toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
      });

      // Clear venue
      const clearVenueButton = screen.getByLabelText('Clear Osteria');
      await user.click(clearVenueButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'venue', 0);

      // Simulate context update after clearing venue
      const updatedContext3: ContextResponse = {
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext3} refreshTrigger={3} />
      );

      // All context cleared, component should not render
      await waitFor(() => {
        expect(screen.queryByText(/Agent Memory/)).not.toBeInTheDocument();
      });
    });

    it('clears all context at once and updates display', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
          { name: 'Vedge', place_id: 'ChIJdef456' },
        ],
      };

      vi.mocked(api.clearContext).mockResolvedValue();

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={mockContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
        expect(screen.getByText(/Looking for:/)).toBeInTheDocument();
        expect(screen.getByText(/Recent venues:/)).toBeInTheDocument();
      });

      // Click Clear All button
      const clearAllButton = screen.getByRole('button', { name: /Clear All/i });
      await user.click(clearAllButton);

      expect(api.clearContext).toHaveBeenCalledWith(mockSessionId);

      // Simulate context update after clearing all
      const emptyContext: ContextResponse = {
        recent_venues: [],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={emptyContext} refreshTrigger={1} />
      );

      // Component should not render when context is empty
      await waitFor(() => {
        expect(screen.queryByText(/Agent Memory/)).not.toBeInTheDocument();
      });
    });

    it('clears specific venue from list and updates display', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        recent_venues: [
          { name: 'Venue A', place_id: 'ChIJa' },
          { name: 'Venue B', place_id: 'ChIJb' },
          { name: 'Venue C', place_id: 'ChIJc' },
        ],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      const { rerender } = render(
        <ContextDisplay sessionId={mockSessionId} context={mockContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Venue A/)).toBeInTheDocument();
        expect(screen.getByText(/Venue B/)).toBeInTheDocument();
        expect(screen.getByText(/Venue C/)).toBeInTheDocument();
      });

      // Clear middle venue (Venue B)
      const clearVenueBButton = screen.getByLabelText('Clear Venue B');
      await user.click(clearVenueBButton);

      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'venue', 1);

      // Simulate context update after clearing Venue B
      const updatedContext: ContextResponse = {
        recent_venues: [
          { name: 'Venue A', place_id: 'ChIJa' },
          { name: 'Venue C', place_id: 'ChIJc' },
        ],
      };

      rerender(
        <ContextDisplay sessionId={mockSessionId} context={updatedContext} refreshTrigger={1} />
      );

      // Venue B should be gone, A and C should remain
      await waitFor(() => {
        expect(screen.getByText(/Venue A/)).toBeInTheDocument();
        expect(screen.queryByText(/Venue B/)).not.toBeInTheDocument();
        expect(screen.getByText(/Venue C/)).toBeInTheDocument();
      });
    });

    it('handles rapid clear operations without race conditions', async () => {
      const user = userEvent.setup();
      const mockContext: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [
          { name: 'Osteria', place_id: 'ChIJabc123' },
        ],
      };

      vi.mocked(api.clearContextItem).mockResolvedValue();

      render(
        <ContextDisplay sessionId={mockSessionId} context={mockContext} refreshTrigger={0} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Location:/)).toBeInTheDocument();
      });

      // Rapidly click multiple clear buttons
      const clearLocationButton = screen.getByLabelText('Clear location');
      const clearQueryButton = screen.getByLabelText('Clear search query');
      const clearVenueButton = screen.getByLabelText('Clear Osteria');

      await user.click(clearLocationButton);
      await user.click(clearQueryButton);
      await user.click(clearVenueButton);

      // All clear operations should be called
      expect(api.clearContextItem).toHaveBeenCalledTimes(3);
      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'location', undefined);
      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'query', undefined);
      expect(api.clearContextItem).toHaveBeenCalledWith(mockSessionId, 'venue', 0);
    });
  });

  describe('Multi-session context isolation', () => {
    it('displays different context for different sessions', async () => {
      const session1Context: ContextResponse = {
        location: 'Philadelphia',
        search_query: 'Italian food',
        recent_venues: [],
      };

      const session2Context: ContextResponse = {
        location: 'New York',
        search_query: 'Sushi',
        recent_venues: [],
      };

      // Render session 1
      const { rerender } = render(
        <ContextDisplay sessionId="session-1" context={session1Context} />
      );

      await waitFor(() => {
        expect(screen.getByText(/Philadelphia/)).toBeInTheDocument();
        expect(screen.getByText(/Italian food/)).toBeInTheDocument();
      });

      // Switch to session 2
      rerender(
        <ContextDisplay sessionId="session-2" context={session2Context} />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Philadelphia/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Italian food/)).not.toBeInTheDocument();
        expect(screen.getByText(/New York/)).toBeInTheDocument();
        expect(screen.getByText(/Sushi/)).toBeInTheDocument();
      });
    });
  });
});

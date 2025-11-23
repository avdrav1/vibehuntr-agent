/**
 * Tests for venue link extraction in Message component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Message } from './Message';
import type { Message as MessageType } from '../types';

describe('Message - Venue Link Extraction', () => {
  it('should extract and display venue website links', () => {
    const message: MessageType = {
      role: 'assistant',
      content: `Found 1 venue for 'Italian restaurants':

1. **Osteria Ama Philly**
   📍 1905 Chestnut St, Philadelphia, PA 19103, USA
   ⭐⭐⭐⭐ 4.8/5 (1745 reviews)
   💰 Price: $$
   🌐 Website: https://www.osteriaamaphilly.com
   🆔 Place ID: ChIJaSuyUYrHxokR-4BpMKOWt1M`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    // Check that the link is rendered
    const link = screen.getByRole('link', { name: /Visit Osteria Ama Philly website/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://www.osteriaamaphilly.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should extract multiple venue links', () => {
    const message: MessageType = {
      role: 'assistant',
      content: `Found 2 venues:

1. **Restaurant One**
   🌐 Website: https://restaurant-one.com
   🆔 Place ID: ChIJabc123

2. **Restaurant Two**
   🌐 Website: https://restaurant-two.com
   🆔 Place ID: ChIJdef456`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    const link1 = screen.getByRole('link', { name: /Visit Restaurant One website/i });
    const link2 = screen.getByRole('link', { name: /Visit Restaurant Two website/i });

    expect(link1).toHaveAttribute('href', 'https://restaurant-one.com');
    expect(link2).toHaveAttribute('href', 'https://restaurant-two.com');
  });

  it('should not display links for user messages', () => {
    const message: MessageType = {
      role: 'user',
      content: `**Test Restaurant**
   🌐 Website: https://test.com
   🆔 Place ID: ChIJtest123`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    const links = screen.queryAllByRole('link');
    expect(links).toHaveLength(0);
  });

  it('should not display links when website is missing', () => {
    const message: MessageType = {
      role: 'assistant',
      content: `**Restaurant Name**
   📍 123 Main St
   🆔 Place ID: ChIJtest123`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    const links = screen.queryAllByRole('link');
    expect(links).toHaveLength(0);
  });

  it('should display links even when Place ID is missing', () => {
    const message: MessageType = {
      role: 'assistant',
      content: `**Restaurant Name**
   📍 123 Main St
   🌐 Website: https://test.com`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    // Should still show link even without Place ID
    const link = screen.getByRole('link', { name: /Visit Restaurant Name website/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://test.com');
  });

  it('should handle messages without venue information', () => {
    const message: MessageType = {
      role: 'assistant',
      content: 'Hello! How can I help you today?',
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    const links = screen.queryAllByRole('link');
    expect(links).toHaveLength(0);
  });

  it('should handle alternative Place ID format', () => {
    const message: MessageType = {
      role: 'assistant',
      content: `**Test Restaurant**
   🌐 Website: https://test.com
   Place ID: ChIJtest123`,
      timestamp: new Date().toISOString(),
    };

    render(<Message message={message} />);

    const link = screen.getByRole('link', { name: /Visit Test Restaurant website/i });
    expect(link).toBeInTheDocument();
  });
});

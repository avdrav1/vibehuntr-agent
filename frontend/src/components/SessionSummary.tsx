/**
 * SessionSummary Component
 * 
 * Displays finalized itinerary with share button for summary URL.
 * Requirements: 4.5
 */

import React, { useState } from 'react';
import type { SessionSummary as SessionSummaryType } from '../types/planningSession';

interface SessionSummaryProps {
  summary: SessionSummaryType;
}

/**
 * SessionSummary Component
 * 
 * Shows the finalized session summary with shareable link.
 * Requirement: 4.5
 */
export function SessionSummary({ summary }: SessionSummaryProps) {
  const [copied, setCopied] = useState(false);

  /**
   * Copy share URL to clipboard
   */
  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(summary.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  /**
   * Format date and time
   */
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      }),
    };
  };

  /**
   * Format finalized date
   */
  const formatFinalizedDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="session-summary-container">
      <div className="summary-header">
        <div className="header-content">
          <span className="finalized-badge">✓ Finalized</span>
          <h2 className="session-name">{summary.session_name}</h2>
          <p className="finalized-date">
            Finalized on {formatFinalizedDate(summary.finalized_at)}
          </p>
        </div>
      </div>

      <div className="summary-section participants-section">
        <h3>Participants ({summary.participants.length})</h3>
        <div className="participants-grid">
          {summary.participants.map((participant) => (
            <div key={participant.id} className="participant-badge">
              <span className="participant-avatar">
                {participant.display_name.charAt(0).toUpperCase()}
              </span>
              <span className="participant-name">{participant.display_name}</span>
              {participant.is_organizer && (
                <span className="organizer-tag">Organizer</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="summary-section itinerary-section">
        <h3>Final Itinerary ({summary.itinerary.length} stops)</h3>
        <div className="itinerary-list">
          {summary.itinerary.map((item, index) => {
            const { date, time } = formatDateTime(item.scheduled_time);
            const isNewDay =
              index === 0 ||
              new Date(item.scheduled_time).toDateString() !==
                new Date(summary.itinerary[index - 1].scheduled_time).toDateString();

            return (
              <div key={item.id} className="summary-item">
                {isNewDay && <div className="day-divider">{date}</div>}
                
                <div className="item-card">
                  <div className="item-number">{index + 1}</div>
                  
                  <div className="item-details">
                    <div className="item-time">{time}</div>
                    <h4 className="venue-name">{item.venue.name}</h4>
                    <p className="venue-address">{item.venue.address}</p>
                    
                    {(item.venue.rating || item.venue.price_level) && (
                      <div className="venue-meta">
                        {item.venue.rating && (
                          <span className="rating">
                            ★ {item.venue.rating.toFixed(1)}
                          </span>
                        )}
                        {item.venue.price_level && (
                          <span className="price">
                            {'$'.repeat(item.venue.price_level)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="summary-actions">
        <button onClick={handleShare} className="share-button" disabled={copied}>
          {copied ? (
            <>
              <span className="button-icon">✓</span>
              Copied!
            </>
          ) : (
            <>
              <span className="button-icon">🔗</span>
              Share Summary
            </>
          )}
        </button>
      </div>

      <style>{`
        .session-summary-container {
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .summary-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 32px 24px;
          text-align: center;
        }

        .finalized-badge {
          display: inline-block;
          background: rgba(255, 255, 255, 0.2);
          padding: 6px 16px;
          border-radius: 16px;
          font-size: 13px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        .session-name {
          margin: 0 0 8px 0;
          font-size: 28px;
          font-weight: 700;
        }

        .finalized-date {
          margin: 0;
          font-size: 14px;
          opacity: 0.9;
        }

        .summary-section {
          padding: 24px;
          border-bottom: 1px solid #e9ecef;
        }

        .summary-section:last-of-type {
          border-bottom: none;
        }

        .summary-section h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
          color: #212529;
        }

        .participants-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 12px;
        }

        .participant-badge {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .participant-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          font-weight: 600;
          flex-shrink: 0;
        }

        .participant-name {
          flex: 1;
          font-size: 14px;
          font-weight: 500;
          color: #212529;
        }

        .organizer-tag {
          background: #ffc107;
          color: #856404;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .itinerary-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .day-divider {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .summary-item {
          display: flex;
          flex-direction: column;
        }

        .item-card {
          display: flex;
          gap: 16px;
          padding: 16px;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 4px solid #667eea;
        }

        .item-number {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          font-weight: 700;
          flex-shrink: 0;
        }

        .item-details {
          flex: 1;
        }

        .item-time {
          font-size: 13px;
          font-weight: 600;
          color: #667eea;
          margin-bottom: 4px;
        }

        .venue-name {
          margin: 0 0 6px 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
        }

        .venue-address {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #6c757d;
        }

        .venue-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
        }

        .rating {
          color: #ffc107;
          font-weight: 600;
        }

        .price {
          color: #28a745;
          font-weight: 600;
        }

        .summary-actions {
          padding: 24px;
          background: #f8f9fa;
          display: flex;
          justify-content: center;
        }

        .share-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 14px 32px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .share-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }

        .share-button:disabled {
          background: #28a745;
          cursor: default;
        }

        .button-icon {
          font-size: 18px;
        }

        @media (max-width: 768px) {
          .summary-header {
            padding: 24px 16px;
          }

          .session-name {
            font-size: 24px;
          }

          .summary-section {
            padding: 16px;
          }

          .participants-grid {
            grid-template-columns: 1fr;
          }

          .item-card {
            flex-direction: column;
            align-items: flex-start;
          }

          .item-number {
            align-self: flex-start;
          }
        }
      `}</style>
    </div>
  );
}

/**
 * ParticipantList Component
 * 
 * Displays all participants in a planning session with their names.
 * Highlights the organizer.
 * 
 * Requirements: 1.4
 */

import React from 'react';
import type { Participant } from '../types/planningSession';

interface ParticipantListProps {
  participants: Participant[];
  currentParticipantId?: string;
}

/**
 * ParticipantList Component
 * 
 * Shows all participants with organizer highlighted.
 * Requirement: 1.4
 */
export function ParticipantList({ participants, currentParticipantId }: ParticipantListProps) {
  // Sort participants: organizer first, then by join time
  const sortedParticipants = [...participants].sort((a, b) => {
    if (a.is_organizer && !b.is_organizer) return -1;
    if (!a.is_organizer && b.is_organizer) return 1;
    return new Date(a.joined_at).getTime() - new Date(b.joined_at).getTime();
  });

  /**
   * Format join time
   */
  const formatJoinTime = (joinedAt: string) => {
    const date = new Date(joinedAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMins > 0) {
      return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  return (
    <div className="participant-list-container">
      <div className="participant-list-header">
        <h3>Participants</h3>
        <span className="participant-count">{participants.length}</span>
      </div>

      <div className="participant-list">
        {sortedParticipants.map((participant) => (
          <div
            key={participant.id}
            className={`participant-item ${
              participant.is_organizer ? 'organizer' : ''
            } ${participant.id === currentParticipantId ? 'current' : ''}`}
          >
            <div className="participant-avatar">
              {participant.display_name.charAt(0).toUpperCase()}
            </div>
            
            <div className="participant-info">
              <div className="participant-name">
                {participant.display_name}
                {participant.id === currentParticipantId && (
                  <span className="you-badge">You</span>
                )}
              </div>
              <div className="participant-meta">
                {participant.is_organizer && (
                  <span className="organizer-badge">Organizer</span>
                )}
                <span className="join-time">
                  Joined {formatJoinTime(participant.joined_at)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {participants.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">👥</span>
          <p>No participants yet</p>
        </div>
      )}

      <style>{`
        .participant-list-container {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
        }

        .participant-list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e9ecef;
        }

        .participant-list-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
        }

        .participant-count {
          background: #e9ecef;
          color: #495057;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 600;
        }

        .participant-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .participant-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 6px;
          transition: background 0.2s;
        }

        .participant-item:hover {
          background: #f8f9fa;
        }

        .participant-item.current {
          background: #e7f3ff;
          border: 1px solid #b3d9ff;
        }

        .participant-item.organizer {
          background: #fff3cd;
        }

        .participant-item.organizer.current {
          background: linear-gradient(135deg, #fff3cd 0%, #e7f3ff 100%);
        }

        .participant-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          font-weight: 600;
          flex-shrink: 0;
        }

        .participant-item.organizer .participant-avatar {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .participant-info {
          flex: 1;
          min-width: 0;
        }

        .participant-name {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 15px;
          font-weight: 600;
          color: #212529;
          margin-bottom: 4px;
        }

        .you-badge {
          background: #007bff;
          color: white;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .participant-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: #6c757d;
        }

        .organizer-badge {
          background: #ffc107;
          color: #856404;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .join-time {
          font-size: 12px;
        }

        .empty-state {
          text-align: center;
          padding: 32px 16px;
          color: #6c757d;
        }

        .empty-icon {
          font-size: 48px;
          display: block;
          margin-bottom: 12px;
        }

        .empty-state p {
          margin: 0;
          font-size: 14px;
        }

        @media (max-width: 600px) {
          .participant-avatar {
            width: 36px;
            height: 36px;
            font-size: 16px;
          }

          .participant-name {
            font-size: 14px;
          }

          .participant-meta {
            font-size: 12px;
          }
        }
      `}</style>
    </div>
  );
}

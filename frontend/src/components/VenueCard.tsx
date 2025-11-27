/**
 * VenueCard Component
 * 
 * Displays venue details from Google Places with voting functionality.
 * Shows vote count and voters.
 * 
 * Requirements: 2.1, 2.2, 2.4
 */

import { useState } from 'react';
import type { RankedVenue, VoteType } from '../types/planningSession';

interface VenueCardProps {
  venue: RankedVenue;
  currentParticipantId?: string;
  onVote?: (voteType: VoteType) => void;
  onAddToItinerary?: () => void;
  onViewComments?: () => void;
  isOrganizer?: boolean;
}

/**
 * VenueCard Component
 * 
 * Shows venue information with voting buttons and vote tallies.
 * Requirements: 2.1, 2.2, 2.4
 */
export function VenueCard({
  venue,
  currentParticipantId,
  onVote,
  onAddToItinerary,
  onViewComments,
  isOrganizer = false,
}: VenueCardProps) {
  const [isVoting, setIsVoting] = useState(false);

  // Get current user's vote
  const currentVote = venue.vote_tally.voters.find(
    (v) => v.participant_id === currentParticipantId
  );

  /**
   * Handle vote button click
   */
  const handleVote = async (voteType: VoteType) => {
    if (!onVote || isVoting) return;

    setIsVoting(true);
    try {
      await onVote(voteType);
    } finally {
      setIsVoting(false);
    }
  };

  /**
   * Render price level
   */
  const renderPriceLevel = () => {
    if (!venue.price_level) return null;
    return '$'.repeat(venue.price_level);
  };

  /**
   * Render rating stars
   */
  const renderRating = () => {
    if (!venue.rating) return null;
    const fullStars = Math.floor(venue.rating);
    const hasHalfStar = venue.rating % 1 >= 0.5;
    
    return (
      <div className="rating">
        {[...Array(fullStars)].map((_, i) => (
          <span key={i} className="star full">★</span>
        ))}
        {hasHalfStar && <span className="star half">★</span>}
        <span className="rating-value">{venue.rating.toFixed(1)}</span>
      </div>
    );
  };

  return (
    <div className="venue-card">
      {venue.photo_url && (
        <div className="venue-photo">
          <img src={venue.photo_url} alt={venue.name} />
          {venue.rank && (
            <div className="rank-badge">#{venue.rank}</div>
          )}
        </div>
      )}

      <div className="venue-content">
        <div className="venue-header">
          <h3 className="venue-name">{venue.name}</h3>
          <div className="venue-meta">
            {renderRating()}
            {venue.price_level && (
              <span className="price-level">{renderPriceLevel()}</span>
            )}
          </div>
        </div>

        <p className="venue-address">{venue.address}</p>

        <div className="voting-section">
          <div className="vote-buttons">
            <button
              onClick={() => handleVote('UPVOTE')}
              className={`vote-button upvote ${
                currentVote?.vote_type === 'UPVOTE' ? 'active' : ''
              }`}
              disabled={isVoting}
              title="Upvote"
            >
              <span className="vote-icon">👍</span>
              <span className="vote-count">{venue.vote_tally.upvotes}</span>
            </button>

            <button
              onClick={() => handleVote('DOWNVOTE')}
              className={`vote-button downvote ${
                currentVote?.vote_type === 'DOWNVOTE' ? 'active' : ''
              }`}
              disabled={isVoting}
              title="Downvote"
            >
              <span className="vote-icon">👎</span>
              <span className="vote-count">{venue.vote_tally.downvotes}</span>
            </button>
          </div>

          {venue.vote_tally.voters.length > 0 && (
            <div className="voters-list">
              <span className="voters-label">Voted:</span>
              {venue.vote_tally.voters.map((voter, index) => (
                <span key={voter.participant_id} className="voter-name">
                  {voter.display_name}
                  {voter.vote_type === 'UPVOTE' ? ' 👍' : ' 👎'}
                  {index < venue.vote_tally.voters.length - 1 && ', '}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="venue-actions">
          {isOrganizer && onAddToItinerary && (
            <button
              onClick={onAddToItinerary}
              className="action-button primary"
            >
              Add to Itinerary
            </button>
          )}
          
          {onViewComments && (
            <button
              onClick={onViewComments}
              className="action-button secondary"
            >
              Comments
            </button>
          )}
        </div>
      </div>

      <style>{`
        .venue-card {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          overflow: hidden;
          transition: box-shadow 0.2s;
        }

        .venue-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .venue-photo {
          position: relative;
          width: 100%;
          height: 200px;
          overflow: hidden;
          background: #f8f9fa;
        }

        .venue-photo img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .rank-badge {
          position: absolute;
          top: 12px;
          right: 12px;
          background: rgba(0, 0, 0, 0.8);
          color: white;
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 14px;
          font-weight: 600;
        }

        .venue-content {
          padding: 16px;
        }

        .venue-header {
          margin-bottom: 8px;
        }

        .venue-name {
          margin: 0 0 8px 0;
          font-size: 18px;
          font-weight: 600;
          color: #212529;
        }

        .venue-meta {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .rating {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .star {
          color: #ffc107;
          font-size: 16px;
        }

        .rating-value {
          margin-left: 4px;
          font-size: 14px;
          font-weight: 600;
          color: #495057;
        }

        .price-level {
          color: #28a745;
          font-size: 14px;
          font-weight: 600;
        }

        .venue-address {
          margin: 0 0 16px 0;
          font-size: 14px;
          color: #6c757d;
        }

        .voting-section {
          margin-bottom: 16px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 6px;
        }

        .vote-buttons {
          display: flex;
          gap: 12px;
          margin-bottom: 12px;
        }

        .vote-button {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 10px 16px;
          border: 2px solid #dee2e6;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 14px;
          font-weight: 600;
        }

        .vote-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .vote-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .vote-button.upvote.active {
          background: #d4edda;
          border-color: #28a745;
          color: #155724;
        }

        .vote-button.downvote.active {
          background: #f8d7da;
          border-color: #dc3545;
          color: #721c24;
        }

        .vote-icon {
          font-size: 18px;
        }

        .vote-count {
          font-size: 16px;
        }

        .voters-list {
          font-size: 13px;
          color: #6c757d;
          line-height: 1.6;
        }

        .voters-label {
          font-weight: 600;
          margin-right: 4px;
        }

        .voter-name {
          color: #495057;
        }

        .venue-actions {
          display: flex;
          gap: 8px;
        }

        .action-button {
          flex: 1;
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-button.primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .action-button.primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .action-button.secondary {
          background: white;
          color: #667eea;
          border: 2px solid #667eea;
        }

        .action-button.secondary:hover {
          background: #f8f9fa;
        }

        @media (max-width: 600px) {
          .venue-photo {
            height: 150px;
          }

          .venue-name {
            font-size: 16px;
          }

          .vote-buttons {
            flex-direction: column;
          }

          .venue-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
}

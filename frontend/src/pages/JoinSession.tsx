/**
 * JoinSession Page
 * 
 * Page for joining a planning session via invite link.
 * Handles display name entry and error states for expired/revoked links.
 * 
 * Requirements: 1.2, 1.3
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { joinSession } from '../services/planningSessionApi';
import { PlanningSessionAPIError } from '../services/planningSessionApi';

/**
 * JoinSession Page Component
 * 
 * Allows users to join a planning session by entering their display name.
 * Requirements: 1.2, 1.3
 */
export function JoinSession() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  
  const [displayName, setDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpired, setIsExpired] = useState(false);
  const [isRevoked, setIsRevoked] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Invalid invite link');
    }
  }, [token]);

  /**
   * Handle form submission
   * Requirement: 1.2
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) {
      setError('Invalid invite link');
      return;
    }

    if (!displayName.trim()) {
      setError('Please enter your name');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await joinSession(token, {
        display_name: displayName.trim(),
      });

      // Store participant info in localStorage for later use
      localStorage.setItem('participant_id', response.participant.id);
      localStorage.setItem('participant_name', response.participant.display_name);
      localStorage.setItem('session_id', response.session.id);

      // Navigate to the session page
      navigate(`/session/${response.session.id}`);
    } catch (err) {
      setIsLoading(false);
      
      if (err instanceof PlanningSessionAPIError) {
        // Handle specific error cases (Requirement 1.3)
        if (err.status === 410 || err.message.includes('expired')) {
          setIsExpired(true);
          setError('This invite link has expired');
        } else if (err.status === 403 || err.message.includes('revoked')) {
          setIsRevoked(true);
          setError('This invite link has been revoked');
        } else if (err.status === 404) {
          setError('Session not found. The invite link may be invalid.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Failed to join session. Please try again.');
      }
      
      console.error('Failed to join session:', err);
    }
  };

  return (
    <div className="join-session-page">
      <div className="join-session-container">
        <div className="join-session-header">
          <h1>Join Planning Session</h1>
          <p>Enter your name to join the collaborative planning session</p>
        </div>

        {isExpired ? (
          <div className="error-state expired">
            <span className="error-icon">⏰</span>
            <h2>Invite Link Expired</h2>
            <p>This invite link has expired and can no longer be used.</p>
            <p>Please ask the organizer for a new invite link.</p>
          </div>
        ) : isRevoked ? (
          <div className="error-state revoked">
            <span className="error-icon">🚫</span>
            <h2>Invite Link Revoked</h2>
            <p>This invite link has been revoked by the organizer.</p>
            <p>Please contact the organizer for more information.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="join-form">
            <div className="form-group">
              <label htmlFor="displayName">Your Name</label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                maxLength={50}
                disabled={isLoading}
                autoFocus
                required
              />
              <span className="form-hint">
                This name will be visible to other participants
              </span>
            </div>

            {error && !isExpired && !isRevoked && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="join-button"
              disabled={isLoading || !displayName.trim()}
            >
              {isLoading ? 'Joining...' : 'Join Session'}
            </button>
          </form>
        )}
      </div>

      <style>{`
        .join-session-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
        }

        .join-session-container {
          background: white;
          border-radius: 12px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
          padding: 40px;
          max-width: 500px;
          width: 100%;
        }

        .join-session-header {
          text-align: center;
          margin-bottom: 32px;
        }

        .join-session-header h1 {
          margin: 0 0 8px 0;
          font-size: 28px;
          font-weight: 700;
          color: #212529;
        }

        .join-session-header p {
          margin: 0;
          font-size: 16px;
          color: #6c757d;
        }

        .error-state {
          text-align: center;
          padding: 32px;
        }

        .error-state .error-icon {
          font-size: 64px;
          display: block;
          margin-bottom: 16px;
        }

        .error-state h2 {
          margin: 0 0 12px 0;
          font-size: 24px;
          font-weight: 600;
          color: #212529;
        }

        .error-state p {
          margin: 8px 0;
          font-size: 16px;
          color: #6c757d;
        }

        .error-state.expired {
          color: #856404;
        }

        .error-state.revoked {
          color: #721c24;
        }

        .join-form {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-group label {
          font-size: 14px;
          font-weight: 600;
          color: #212529;
        }

        .form-group input {
          padding: 12px 16px;
          border: 2px solid #dee2e6;
          border-radius: 8px;
          font-size: 16px;
          transition: border-color 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #667eea;
        }

        .form-group input:disabled {
          background: #f8f9fa;
          cursor: not-allowed;
        }

        .form-hint {
          font-size: 13px;
          color: #6c757d;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 6px;
          color: #721c24;
          font-size: 14px;
        }

        .error-message .error-icon {
          font-size: 18px;
        }

        .join-button {
          padding: 14px 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .join-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .join-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        @media (max-width: 600px) {
          .join-session-container {
            padding: 24px;
          }

          .join-session-header h1 {
            font-size: 24px;
          }

          .join-session-header p {
            font-size: 14px;
          }
        }
      `}</style>
    </div>
  );
}

/**
 * InviteLink Component
 * 
 * Displays a shareable invite link with copy functionality and expiration status.
 * Requirements: 1.1
 */

import React, { useState } from 'react';
import type { PlanningSession } from '../types/planningSession';

interface InviteLinkProps {
  session: PlanningSession;
  onRevoke?: () => void;
  isOrganizer?: boolean;
}

/**
 * InviteLink Component
 * 
 * Shows the invite link with copy button and expiration info.
 * Requirement: 1.1
 */
export function InviteLink({ session, onRevoke, isOrganizer = false }: InviteLinkProps) {
  const [copied, setCopied] = useState(false);

  // Generate the full invite URL
  const inviteUrl = `${window.location.origin}/join/${session.invite_token}`;

  // Check if invite is expired
  const expiresAt = new Date(session.invite_expires_at);
  const now = new Date();
  const isExpired = now > expiresAt;
  const isRevoked = session.invite_revoked;

  /**
   * Copy invite link to clipboard
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  /**
   * Format expiration time
   */
  const formatExpiration = () => {
    const diffMs = expiresAt.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `Expires in ${diffDays} day${diffDays > 1 ? 's' : ''}`;
    } else if (diffHours > 0) {
      return `Expires in ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    } else {
      return 'Expires soon';
    }
  };

  return (
    <div className="invite-link-container">
      <div className="invite-link-header">
        <h3>Invite Link</h3>
        {isOrganizer && !isRevoked && !isExpired && onRevoke && (
          <button
            onClick={onRevoke}
            className="revoke-button"
            title="Revoke invite link"
          >
            Revoke
          </button>
        )}
      </div>

      {isRevoked ? (
        <div className="invite-status revoked">
          <span className="status-icon">🚫</span>
          <span>This invite link has been revoked</span>
        </div>
      ) : isExpired ? (
        <div className="invite-status expired">
          <span className="status-icon">⏰</span>
          <span>This invite link has expired</span>
        </div>
      ) : (
        <>
          <div className="invite-link-display">
            <input
              type="text"
              value={inviteUrl}
              readOnly
              className="invite-url-input"
            />
            <button
              onClick={handleCopy}
              className="copy-button"
              disabled={copied}
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>

          <div className="invite-expiration">
            <span className="expiration-icon">⏱️</span>
            <span className="expiration-text">{formatExpiration()}</span>
          </div>
        </>
      )}

      <style>{`
        .invite-link-container {
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          margin: 16px 0;
        }

        .invite-link-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .invite-link-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
        }

        .revoke-button {
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 4px;
          padding: 6px 12px;
          font-size: 14px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .revoke-button:hover {
          background: #c82333;
        }

        .invite-status {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          border-radius: 6px;
          font-size: 14px;
        }

        .invite-status.revoked {
          background: #f8d7da;
          color: #721c24;
        }

        .invite-status.expired {
          background: #fff3cd;
          color: #856404;
        }

        .status-icon {
          font-size: 18px;
        }

        .invite-link-display {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }

        .invite-url-input {
          flex: 1;
          padding: 10px 12px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          font-size: 14px;
          font-family: monospace;
          background: white;
          color: #495057;
        }

        .invite-url-input:focus {
          outline: none;
          border-color: #80bdff;
          box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }

        .copy-button {
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          padding: 10px 20px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
          white-space: nowrap;
        }

        .copy-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .copy-button:disabled {
          background: #28a745;
          cursor: default;
        }

        .invite-expiration {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: #6c757d;
        }

        .expiration-icon {
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}

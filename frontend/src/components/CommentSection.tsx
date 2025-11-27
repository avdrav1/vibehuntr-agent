/**
 * CommentSection Component
 * 
 * Displays comments chronologically with add comment form and character counter.
 * Requirements: 6.1, 6.2
 */

import React, { useState } from 'react';
import type { Comment } from '../types/planningSession';

interface CommentSectionProps {
  comments: Comment[];
  venueId: string;
  currentParticipantId?: string;
  onAddComment?: (text: string) => void;
}

const MAX_COMMENT_LENGTH = 500;

/**
 * CommentSection Component
 * 
 * Shows comments in chronological order with add comment functionality.
 * Requirements: 6.1, 6.2
 */
export function CommentSection({
  comments,
  venueId: _venueId,
  currentParticipantId,
  onAddComment,
}: CommentSectionProps) {
  // venueId available as _venueId for future use
  const [commentText, setCommentText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle comment submission
   * Requirement: 6.1
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!commentText.trim()) {
      return;
    }

    if (commentText.length > MAX_COMMENT_LENGTH) {
      setError(`Comment must be ${MAX_COMMENT_LENGTH} characters or less`);
      return;
    }

    if (!onAddComment) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onAddComment(commentText.trim());
      setCommentText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add comment');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Format timestamp
   */
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else if (diffMins > 0) {
      return `${diffMins}m ago`;
    } else {
      return 'Just now';
    }
  };

  const remainingChars = MAX_COMMENT_LENGTH - commentText.length;
  const isOverLimit = remainingChars < 0;

  return (
    <div className="comment-section-container">
      <div className="comment-section-header">
        <h4>Comments</h4>
        <span className="comment-count">{comments.length}</span>
      </div>

      {/* Comment List - Requirement 6.2: Chronological order */}
      <div className="comments-list">
        {comments.length === 0 ? (
          <div className="empty-comments">
            <span className="empty-icon">💬</span>
            <p>No comments yet. Be the first to share your thoughts!</p>
          </div>
        ) : (
          comments.map((comment) => (
            <div
              key={comment.id}
              className={`comment-item ${
                comment.participant_id === currentParticipantId ? 'own-comment' : ''
              }`}
            >
              <div className="comment-header">
                <span className="comment-author">{comment.participant_name}</span>
                <span className="comment-time">{formatTimestamp(comment.created_at)}</span>
              </div>
              <p className="comment-text">{comment.text}</p>
            </div>
          ))
        )}
      </div>

      {/* Add Comment Form - Requirement 6.1 */}
      {currentParticipantId && onAddComment && (
        <form onSubmit={handleSubmit} className="add-comment-form">
          <div className="form-group">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Add your comment..."
              className={`comment-input ${isOverLimit ? 'over-limit' : ''}`}
              rows={3}
              disabled={isSubmitting}
            />
            <div className="form-footer">
              <span
                className={`char-counter ${
                  remainingChars < 50 ? 'warning' : ''
                } ${isOverLimit ? 'error' : ''}`}
              >
                {remainingChars} characters remaining
              </span>
              <button
                type="submit"
                className="submit-button"
                disabled={isSubmitting || !commentText.trim() || isOverLimit}
              >
                {isSubmitting ? 'Posting...' : 'Post Comment'}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}
        </form>
      )}

      <style>{`
        .comment-section-container {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
        }

        .comment-section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e9ecef;
        }

        .comment-section-header h4 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
        }

        .comment-count {
          background: #e9ecef;
          color: #495057;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 600;
        }

        .comments-list {
          max-height: 400px;
          overflow-y: auto;
          margin-bottom: 16px;
        }

        .empty-comments {
          text-align: center;
          padding: 32px 16px;
          color: #6c757d;
        }

        .empty-icon {
          font-size: 48px;
          display: block;
          margin-bottom: 12px;
        }

        .empty-comments p {
          margin: 0;
          font-size: 14px;
        }

        .comment-item {
          padding: 12px;
          margin-bottom: 12px;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 3px solid #dee2e6;
        }

        .comment-item.own-comment {
          background: #e7f3ff;
          border-left-color: #007bff;
        }

        .comment-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .comment-author {
          font-size: 14px;
          font-weight: 600;
          color: #212529;
        }

        .comment-time {
          font-size: 12px;
          color: #6c757d;
        }

        .comment-text {
          margin: 0;
          font-size: 14px;
          color: #495057;
          line-height: 1.5;
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .add-comment-form {
          border-top: 1px solid #e9ecef;
          padding-top: 16px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .comment-input {
          width: 100%;
          padding: 12px;
          border: 2px solid #dee2e6;
          border-radius: 6px;
          font-size: 14px;
          font-family: inherit;
          resize: vertical;
          transition: border-color 0.2s;
        }

        .comment-input:focus {
          outline: none;
          border-color: #667eea;
        }

        .comment-input.over-limit {
          border-color: #dc3545;
        }

        .comment-input:disabled {
          background: #f8f9fa;
          cursor: not-allowed;
        }

        .form-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .char-counter {
          font-size: 13px;
          color: #6c757d;
        }

        .char-counter.warning {
          color: #ffc107;
          font-weight: 600;
        }

        .char-counter.error {
          color: #dc3545;
          font-weight: 600;
        }

        .submit-button {
          padding: 8px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .submit-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .submit-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 6px;
          color: #721c24;
          font-size: 13px;
          margin-top: 8px;
        }

        .error-icon {
          font-size: 16px;
        }

        @media (max-width: 600px) {
          .comment-section-container {
            padding: 12px;
          }

          .comments-list {
            max-height: 300px;
          }

          .form-footer {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .submit-button {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

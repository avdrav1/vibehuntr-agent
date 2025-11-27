/**
 * ItineraryView Component
 * 
 * Displays itinerary items in chronological order.
 * Allows organizer to add/remove items.
 * 
 * Requirements: 3.2, 4.2
 */

import type { ItineraryItem } from '../types/planningSession';

interface ItineraryViewProps {
  items: ItineraryItem[];
  isOrganizer?: boolean;
  onRemove?: (itemId: string) => void;
}

/**
 * ItineraryView Component
 * 
 * Shows itinerary in chronological order with management controls.
 * Requirements: 3.2, 4.2
 */
export function ItineraryView({
  items,
  isOrganizer = false,
  onRemove,
}: ItineraryViewProps) {
  /**
   * Format time for display
   */
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  /**
   * Group items by date
   */
  const groupByDate = () => {
    const groups: Record<string, ItineraryItem[]> = {};
    
    items.forEach((item) => {
      const dateKey = new Date(item.scheduled_time).toDateString();
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(item);
    });

    return Object.entries(groups).map(([dateKey, dateItems]) => ({
      date: new Date(dateKey),
      items: dateItems.sort(
        (a, b) =>
          new Date(a.scheduled_time).getTime() -
          new Date(b.scheduled_time).getTime()
      ),
    }));
  };

  const groupedItems = groupByDate();

  return (
    <div className="itinerary-view-container">
      <div className="itinerary-header">
        <h3>Itinerary</h3>
        <span className="item-count">{items.length} stop{items.length !== 1 ? 's' : ''}</span>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📅</span>
          <p>No items in itinerary yet</p>
          {isOrganizer && (
            <p className="empty-hint">
              Add venues from the voting section to build your itinerary
            </p>
          )}
        </div>
      ) : (
        <div className="itinerary-timeline">
          {groupedItems.map((group, groupIndex) => (
            <div key={groupIndex} className="date-group">
              <div className="date-header">
                <span className="date-label">{formatDate(group.date.toISOString())}</span>
              </div>

              <div className="items-list">
                {group.items.map((item, itemIndex) => (
                  <div key={item.id} className="itinerary-item">
                    <div className="timeline-marker">
                      <div className="marker-dot"></div>
                      {itemIndex < group.items.length - 1 && (
                        <div className="marker-line"></div>
                      )}
                    </div>

                    <div className="item-content">
                      <div className="item-time">{formatTime(item.scheduled_time)}</div>
                      
                      <div className="item-card">
                        <div className="item-header">
                          <h4 className="venue-name">{item.venue.name}</h4>
                          {isOrganizer && onRemove && (
                            <button
                              onClick={() => onRemove(item.id)}
                              className="remove-button"
                              title="Remove from itinerary"
                            >
                              ✕
                            </button>
                          )}
                        </div>

                        <p className="venue-address">{item.venue.address}</p>

                        {item.venue.rating && (
                          <div className="venue-rating">
                            <span className="star">★</span>
                            <span>{item.venue.rating.toFixed(1)}</span>
                            {item.venue.price_level && (
                              <span className="price-level">
                                {' • '}{'$'.repeat(item.venue.price_level)}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        .itinerary-view-container {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
        }

        .itinerary-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e9ecef;
        }

        .itinerary-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
        }

        .item-count {
          background: #e9ecef;
          color: #495057;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 13px;
          font-weight: 600;
        }

        .empty-state {
          text-align: center;
          padding: 48px 16px;
          color: #6c757d;
        }

        .empty-icon {
          font-size: 64px;
          display: block;
          margin-bottom: 16px;
        }

        .empty-state p {
          margin: 8px 0;
          font-size: 14px;
        }

        .empty-hint {
          color: #adb5bd;
          font-size: 13px;
        }

        .itinerary-timeline {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .date-group {
          display: flex;
          flex-direction: column;
        }

        .date-header {
          margin-bottom: 16px;
        }

        .date-label {
          display: inline-block;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 6px 16px;
          border-radius: 16px;
          font-size: 13px;
          font-weight: 600;
        }

        .items-list {
          display: flex;
          flex-direction: column;
        }

        .itinerary-item {
          display: flex;
          gap: 16px;
          position: relative;
        }

        .timeline-marker {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding-top: 8px;
        }

        .marker-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: 3px solid white;
          box-shadow: 0 0 0 2px #667eea;
          flex-shrink: 0;
        }

        .marker-line {
          width: 2px;
          flex: 1;
          background: #dee2e6;
          margin-top: 4px;
          min-height: 40px;
        }

        .item-content {
          flex: 1;
          padding-bottom: 24px;
        }

        .item-time {
          font-size: 13px;
          font-weight: 600;
          color: #667eea;
          margin-bottom: 8px;
        }

        .item-card {
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          transition: box-shadow 0.2s;
        }

        .item-card:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .venue-name {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #212529;
          flex: 1;
        }

        .remove-button {
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 4px;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 14px;
          transition: background 0.2s;
          flex-shrink: 0;
        }

        .remove-button:hover {
          background: #c82333;
        }

        .venue-address {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #6c757d;
        }

        .venue-rating {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
          color: #495057;
        }

        .star {
          color: #ffc107;
          font-size: 16px;
        }

        .price-level {
          color: #28a745;
          font-weight: 600;
        }

        @media (max-width: 600px) {
          .itinerary-item {
            gap: 12px;
          }

          .item-card {
            padding: 12px;
          }

          .venue-name {
            font-size: 15px;
          }
        }
      `}</style>
    </div>
  );
}

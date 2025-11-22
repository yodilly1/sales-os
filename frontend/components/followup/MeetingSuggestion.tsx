'use client';

import React, { useState } from 'react';
import { FollowUpMeetingSuggestion, MeetingType } from './types';

interface MeetingSuggestionProps {
  suggestion: FollowUpMeetingSuggestion;
  onBook?: (selectedDate: Date) => void;
  onDismiss?: () => void;
  onEdit?: (updates: Partial<FollowUpMeetingSuggestion>) => void;
}

const meetingTypeLabels: Record<MeetingType, string> = {
  discovery: 'Discovery Call',
  demo: 'Product Demo',
  technical_deep_dive: 'Technical Deep Dive',
  proposal_review: 'Proposal Review',
  negotiation: 'Negotiation',
  executive_briefing: 'Executive Briefing',
  check_in: 'Check-in',
  onboarding: 'Onboarding',
};

const meetingTypeIcons: Record<MeetingType, string> = {
  discovery: '🔍',
  demo: '🎯',
  technical_deep_dive: '⚙️',
  proposal_review: '📋',
  negotiation: '🤝',
  executive_briefing: '👔',
  check_in: '📞',
  onboarding: '🚀',
};

export function MeetingSuggestion({
  suggestion,
  onBook,
  onDismiss,
  onEdit,
}: MeetingSuggestionProps) {
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [customDate, setCustomDate] = useState('');
  const [customTime, setCustomTime] = useState('');

  const { suggestion: meeting } = suggestion;
  const isBooked = !!suggestion.bookedAt;

  function handleDateSelect(date: Date) {
    setSelectedDate(date);
    setShowDatePicker(false);
  }

  function handleBook() {
    if (selectedDate) {
      onBook?.(selectedDate);
    } else if (customDate && customTime) {
      const date = new Date(`${customDate}T${customTime}`);
      onBook?.(date);
    }
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  }

  function formatTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  }

  return (
    <div className={`meeting-suggestion ${isBooked ? 'booked' : ''}`}>
      {/* Header */}
      <div className="header">
        <div className="type-info">
          <span className="type-icon">{meetingTypeIcons[meeting.meetingType]}</span>
          <span className="type-label">{meetingTypeLabels[meeting.meetingType]}</span>
        </div>

        {isBooked && (
          <span className="booked-badge">Booked</span>
        )}

        {!isBooked && onDismiss && (
          <button onClick={onDismiss} className="dismiss-btn">
            Dismiss
          </button>
        )}
      </div>

      {/* Title and description */}
      <h3 className="title">{meeting.title}</h3>
      <p className="description">{meeting.description}</p>

      {/* Meeting details */}
      <div className="details">
        <div className="detail-item">
          <span className="detail-label">Duration</span>
          <span className="detail-value">{meeting.suggestedDurationMinutes} minutes</span>
        </div>

        {meeting.suggestedAttendees.length > 0 && (
          <div className="detail-item">
            <span className="detail-label">Attendees</span>
            <span className="detail-value">{meeting.suggestedAttendees.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Agenda */}
      {meeting.agenda.length > 0 && (
        <div className="agenda-section">
          <h4>Suggested Agenda</h4>
          <ol className="agenda-list">
            {meeting.agenda.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Reasoning */}
      <div className="reasoning-section">
        <h4>Why this meeting?</h4>
        <p>{meeting.reasoning}</p>

        {meeting.spicedFocusAreas.length > 0 && (
          <div className="focus-areas">
            <span className="label">SPICED focus:</span>
            {meeting.spicedFocusAreas.map((area) => (
              <span key={area} className="focus-tag">{area}</span>
            ))}
          </div>
        )}
      </div>

      {/* Date selection */}
      {!isBooked && (
        <div className="booking-section">
          <h4>Suggested Times</h4>

          <div className="suggested-dates">
            {meeting.suggestedDates.map((dateStr, index) => {
              const date = new Date(dateStr);
              const isSelected = selectedDate?.getTime() === date.getTime();

              return (
                <button
                  key={index}
                  className={`date-option ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleDateSelect(date)}
                >
                  <span className="date">{formatDate(dateStr)}</span>
                  <span className="time">{formatTime(dateStr)}</span>
                </button>
              );
            })}
          </div>

          <div className="custom-date">
            <button
              className="custom-date-toggle"
              onClick={() => setShowDatePicker(!showDatePicker)}
            >
              {showDatePicker ? 'Hide custom time' : 'Choose custom time'}
            </button>

            {showDatePicker && (
              <div className="custom-date-picker">
                <input
                  type="date"
                  value={customDate}
                  onChange={(e) => setCustomDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                />
                <input
                  type="time"
                  value={customTime}
                  onChange={(e) => setCustomTime(e.target.value)}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Booked info */}
      {isBooked && suggestion.bookedAt && (
        <div className="booked-info">
          <span className="booked-label">Scheduled for:</span>
          <span className="booked-date">
            {formatDate(suggestion.bookedAt)} at {formatTime(suggestion.bookedAt)}
          </span>
          {suggestion.bookingLink && (
            <a
              href={suggestion.bookingLink}
              target="_blank"
              rel="noopener noreferrer"
              className="booking-link"
            >
              Open Calendar Event
            </a>
          )}
        </div>
      )}

      {/* Actions */}
      {!isBooked && onBook && (selectedDate || (customDate && customTime)) && (
        <div className="actions">
          <button onClick={handleBook} className="btn-book">
            Book Meeting
          </button>
        </div>
      )}

      <style jsx>{`
        .meeting-suggestion {
          padding: 1.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .meeting-suggestion.booked {
          background: #f0fdf4;
          border-color: #86efac;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .type-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .type-icon {
          font-size: 1.25rem;
        }

        .type-label {
          font-size: 0.875rem;
          font-weight: 500;
          color: #64748b;
        }

        .booked-badge {
          padding: 0.25rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: #166534;
          background: #dcfce7;
          border-radius: 9999px;
        }

        .dismiss-btn {
          padding: 0.375rem 0.75rem;
          font-size: 0.875rem;
          color: #64748b;
          background: transparent;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        .title {
          margin: 0 0 0.5rem 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: #1e293b;
        }

        .description {
          margin: 0 0 1rem 0;
          font-size: 0.875rem;
          color: #64748b;
          line-height: 1.5;
        }

        .details {
          display: flex;
          gap: 2rem;
          margin-bottom: 1rem;
          padding: 0.75rem;
          background: #f8fafc;
          border-radius: 0.375rem;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .detail-label {
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .detail-value {
          font-size: 0.875rem;
          font-weight: 500;
          color: #1e293b;
        }

        .agenda-section,
        .reasoning-section {
          margin-bottom: 1rem;
        }

        .agenda-section h4,
        .reasoning-section h4 {
          margin: 0 0 0.5rem 0;
          font-size: 0.875rem;
          font-weight: 600;
          color: #475569;
        }

        .agenda-list {
          margin: 0;
          padding-left: 1.25rem;
          font-size: 0.875rem;
          color: #1e293b;
          line-height: 1.6;
        }

        .reasoning-section p {
          margin: 0 0 0.5rem 0;
          font-size: 0.875rem;
          color: #64748b;
        }

        .focus-areas {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .focus-areas .label {
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .focus-tag {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          color: #7c3aed;
          background: #ede9fe;
          border-radius: 0.25rem;
          text-transform: capitalize;
        }

        .booking-section {
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .booking-section h4 {
          margin: 0 0 0.75rem 0;
          font-size: 0.875rem;
          font-weight: 600;
          color: #475569;
        }

        .suggested-dates {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
          margin-bottom: 1rem;
        }

        .date-option {
          display: flex;
          flex-direction: column;
          padding: 0.75rem 1rem;
          background: #f8fafc;
          border: 2px solid transparent;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .date-option:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
        }

        .date-option.selected {
          background: #eff6ff;
          border-color: #3b82f6;
        }

        .date-option .date {
          font-size: 0.875rem;
          font-weight: 500;
          color: #1e293b;
        }

        .date-option .time {
          font-size: 0.75rem;
          color: #64748b;
        }

        .custom-date {
          margin-top: 0.75rem;
        }

        .custom-date-toggle {
          padding: 0.375rem 0.75rem;
          font-size: 0.875rem;
          color: #3b82f6;
          background: transparent;
          border: none;
          cursor: pointer;
        }

        .custom-date-picker {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .custom-date-picker input {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
        }

        .booked-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          background: #dcfce7;
          border-radius: 0.375rem;
        }

        .booked-label {
          font-size: 0.875rem;
          color: #166534;
        }

        .booked-date {
          font-size: 0.875rem;
          font-weight: 600;
          color: #166534;
        }

        .booking-link {
          margin-left: auto;
          font-size: 0.875rem;
          color: #3b82f6;
          text-decoration: none;
        }

        .booking-link:hover {
          text-decoration: underline;
        }

        .actions {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .btn-book {
          padding: 0.75rem 1.5rem;
          font-weight: 500;
          color: white;
          background: #3b82f6;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-book:hover {
          background: #2563eb;
        }
      `}</style>
    </div>
  );
}

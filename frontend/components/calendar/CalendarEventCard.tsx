'use client';

/**
 * CalendarEventCard Component
 *
 * Displays a single calendar event with attendees, meeting link,
 * and transcript linking options.
 */

import React from 'react';
import { CalendarEvent, CalendarProvider } from './types';

interface CalendarEventCardProps {
  event: CalendarEvent;
  onLinkTranscript?: (eventId: string) => void;
  onViewTranscript?: (transcriptId: string) => void;
  compact?: boolean;
}

const providerIcons: Record<CalendarProvider, string> = {
  google: '📅',
  outlook: '📆',
};

export function CalendarEventCard({
  event,
  onLinkTranscript,
  onViewTranscript,
  compact = false,
}: CalendarEventCardProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const formatDate = (date: Date) => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    }

    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    }).format(date);
  };

  const formatDuration = (start: Date, end: Date) => {
    const diff = end.getTime() - start.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) return `${hours}h`;
    return `${hours}h ${remainingMinutes}m`;
  };

  const getAttendeeInitials = (name: string | undefined, email: string) => {
    if (name) {
      const parts = name.split(' ');
      return parts.length > 1
        ? `${parts[0][0]}${parts[parts.length - 1][0]}`
        : name.substring(0, 2);
    }
    return email.substring(0, 2).toUpperCase();
  };

  if (compact) {
    return (
      <div className="event-card-compact">
        <div className="time-block">
          <span className="time">{formatTime(event.startTime)}</span>
          <span className="duration">{formatDuration(event.startTime, event.endTime)}</span>
        </div>
        <div className="event-details">
          <h4 className="event-title">{event.title}</h4>
          <div className="event-meta">
            <span className="attendees-count">
              {event.attendees.length} attendee{event.attendees.length !== 1 ? 's' : ''}
            </span>
            {event.hasTranscript && (
              <span className="transcript-badge">Has transcript</span>
            )}
          </div>
        </div>
        <span className="provider-icon">{providerIcons[event.provider]}</span>

        <style jsx>{`
          .event-card-compact {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px;
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            transition: box-shadow 0.2s;
          }

          .event-card-compact:hover {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          }

          .time-block {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 60px;
          }

          .time {
            font-size: 14px;
            font-weight: 600;
            color: #111827;
          }

          .duration {
            font-size: 12px;
            color: #6B7280;
          }

          .event-details {
            flex: 1;
            min-width: 0;
          }

          .event-title {
            font-size: 14px;
            font-weight: 500;
            color: #111827;
            margin: 0 0 4px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .event-meta {
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .attendees-count {
            font-size: 12px;
            color: #6B7280;
          }

          .transcript-badge {
            font-size: 11px;
            padding: 2px 6px;
            background: #DBEAFE;
            color: #1D4ED8;
            border-radius: 4px;
          }

          .provider-icon {
            font-size: 20px;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="event-card">
      <div className="event-header">
        <div className="event-time">
          <span className="date">{formatDate(event.startTime)}</span>
          <span className="time-range">
            {formatTime(event.startTime)} - {formatTime(event.endTime)}
          </span>
        </div>
        <span className="provider-icon">{providerIcons[event.provider]}</span>
      </div>

      <h3 className="event-title">{event.title}</h3>

      {event.description && (
        <p className="event-description">{event.description}</p>
      )}

      {event.location && (
        <div className="event-location">
          <span className="location-icon">📍</span>
          <span>{event.location}</span>
        </div>
      )}

      {event.meetingLink && (
        <a
          href={event.meetingLink.url}
          target="_blank"
          rel="noopener noreferrer"
          className="meeting-link"
        >
          <span className="link-icon">🔗</span>
          <span>Join {event.meetingLink.provider || 'Meeting'}</span>
        </a>
      )}

      {event.attendees.length > 0 && (
        <div className="attendees-section">
          <span className="attendees-label">Attendees ({event.attendees.length})</span>
          <div className="attendees-list">
            {event.attendees.slice(0, 5).map((attendee, index) => (
              <div
                key={attendee.email}
                className="attendee-avatar"
                title={attendee.name || attendee.email}
                style={{ zIndex: 5 - index }}
              >
                {getAttendeeInitials(attendee.name, attendee.email)}
              </div>
            ))}
            {event.attendees.length > 5 && (
              <div className="attendee-overflow">
                +{event.attendees.length - 5}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="event-actions">
        {event.hasTranscript && event.transcriptId ? (
          <button
            className="btn btn-primary"
            onClick={() => onViewTranscript?.(event.transcriptId!)}
          >
            View Transcript
          </button>
        ) : (
          <button
            className="btn btn-secondary"
            onClick={() => onLinkTranscript?.(event.id)}
          >
            Link Transcript
          </button>
        )}

        {event.htmlLink && (
          <a
            href={event.htmlLink}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            Open in Calendar
          </a>
        )}
      </div>

      <style jsx>{`
        .event-card {
          background: white;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .event-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .event-time {
          display: flex;
          flex-direction: column;
        }

        .date {
          font-size: 12px;
          font-weight: 600;
          color: #6366F1;
          text-transform: uppercase;
        }

        .time-range {
          font-size: 14px;
          color: #6B7280;
        }

        .provider-icon {
          font-size: 24px;
        }

        .event-title {
          font-size: 18px;
          font-weight: 600;
          color: #111827;
          margin: 0 0 8px 0;
        }

        .event-description {
          font-size: 14px;
          color: #6B7280;
          margin: 0 0 12px 0;
          line-height: 1.5;
        }

        .event-location,
        .meeting-link {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #6B7280;
          margin-bottom: 8px;
        }

        .meeting-link {
          color: #2563EB;
          text-decoration: none;
        }

        .meeting-link:hover {
          text-decoration: underline;
        }

        .location-icon,
        .link-icon {
          font-size: 16px;
        }

        .attendees-section {
          margin: 16px 0;
        }

        .attendees-label {
          font-size: 12px;
          font-weight: 500;
          color: #6B7280;
          display: block;
          margin-bottom: 8px;
        }

        .attendees-list {
          display: flex;
          align-items: center;
        }

        .attendee-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366F1, #8B5CF6);
          color: white;
          font-size: 12px;
          font-weight: 500;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid white;
          margin-left: -8px;
          position: relative;
        }

        .attendee-avatar:first-child {
          margin-left: 0;
        }

        .attendee-overflow {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #E5E7EB;
          color: #6B7280;
          font-size: 11px;
          font-weight: 500;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid white;
          margin-left: -8px;
        }

        .event-actions {
          display: flex;
          gap: 8px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #F3F4F6;
        }

        .btn {
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }

        .btn-primary {
          background: #6366F1;
          color: white;
        }

        .btn-primary:hover {
          background: #4F46E5;
        }

        .btn-secondary {
          background: #F3F4F6;
          color: #374151;
        }

        .btn-secondary:hover {
          background: #E5E7EB;
        }
      `}</style>
    </div>
  );
}

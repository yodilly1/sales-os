'use client';

/**
 * UpcomingMeetingsWidget Component
 *
 * Dashboard widget showing upcoming meetings with quick actions.
 */

import React, { useState, useEffect } from 'react';
import {
  CalendarProvider,
  CalendarWidgetData,
  UpcomingMeeting,
} from './types';

interface UpcomingMeetingsWidgetProps {
  data?: CalendarWidgetData;
  onRefresh?: () => Promise<void>;
  onConnectCalendar?: () => void;
  onViewEvent?: (eventId: string) => void;
  onJoinMeeting?: (meetingLink: string) => void;
  onViewAllEvents?: () => void;
  loading?: boolean;
}

const providerIcons: Record<CalendarProvider, string> = {
  google: '📅',
  outlook: '📆',
};

export function UpcomingMeetingsWidget({
  data,
  onRefresh,
  onConnectCalendar,
  onViewEvent,
  onJoinMeeting,
  onViewAllEvents,
  loading = false,
}: UpcomingMeetingsWidgetProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    if (!onRefresh || isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatTimeUntil = (startTime: Date) => {
    const diff = startTime.getTime() - currentTime.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 0) return 'Now';
    if (minutes === 0) return 'Starting';
    if (minutes < 60) return `in ${minutes}m`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `in ${hours}h`;

    const days = Math.floor(hours / 24);
    return `in ${days}d`;
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const isHappeningSoon = (startTime: Date) => {
    const diff = startTime.getTime() - currentTime.getTime();
    const minutes = Math.floor(diff / 60000);
    return minutes <= 15 && minutes >= -5;
  };

  const isHappeningNow = (startTime: Date, endTime: Date) => {
    return currentTime >= startTime && currentTime <= endTime;
  };

  // No data and not connected
  if (!data || data.totalIntegrations === 0) {
    return (
      <div className="widget widget-empty">
        <div className="widget-header">
          <h3>Upcoming Meetings</h3>
        </div>
        <div className="widget-body">
          <div className="empty-state">
            <span className="empty-icon">📅</span>
            <p>Connect your calendar to see upcoming meetings</p>
            {onConnectCalendar && (
              <button className="btn btn-primary" onClick={onConnectCalendar}>
                Connect Calendar
              </button>
            )}
          </div>
        </div>

        <style jsx>{`
          .widget {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            overflow: hidden;
          }

          .widget-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #E5E7EB;
          }

          .widget-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #111827;
          }

          .widget-body {
            padding: 20px;
          }

          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 32px;
            text-align: center;
          }

          .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }

          .empty-state p {
            color: #6B7280;
            font-size: 14px;
            margin: 0 0 16px 0;
          }

          .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
          }

          .btn-primary {
            background: #6366F1;
            color: white;
          }

          .btn-primary:hover {
            background: #4F46E5;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <h3>Upcoming Meetings</h3>
        <div className="header-actions">
          <button
            className="refresh-btn"
            onClick={handleRefresh}
            disabled={isRefreshing || loading}
            title="Refresh"
          >
            <span className={isRefreshing ? 'spinning' : ''}>↻</span>
          </button>
        </div>
      </div>

      <div className="widget-stats">
        <div className="stat">
          <span className="stat-value">{data.meetingsToday}</span>
          <span className="stat-label">Today</span>
        </div>
        <div className="stat">
          <span className="stat-value">{data.meetingsThisWeek}</span>
          <span className="stat-label">This Week</span>
        </div>
        <div className="stat">
          <span className="stat-value">{data.totalIntegrations}</span>
          <span className="stat-label">Calendars</span>
        </div>
      </div>

      {data.nextMeeting && (
        <div
          className={`next-meeting ${
            isHappeningSoon(data.nextMeeting.startTime) ? 'happening-soon' : ''
          } ${
            isHappeningNow(data.nextMeeting.startTime, data.nextMeeting.endTime)
              ? 'happening-now'
              : ''
          }`}
        >
          <div className="next-meeting-header">
            <span className="next-label">
              {isHappeningNow(data.nextMeeting.startTime, data.nextMeeting.endTime)
                ? 'Happening Now'
                : 'Next Up'}
            </span>
            <span className="time-until">
              {formatTimeUntil(data.nextMeeting.startTime)}
            </span>
          </div>
          <h4 className="next-title">{data.nextMeeting.title}</h4>
          <div className="next-meta">
            <span>{formatTime(data.nextMeeting.startTime)}</span>
            <span className="dot">•</span>
            <span>{data.nextMeeting.attendeesCount} attendees</span>
            <span className="provider-icon">
              {providerIcons[data.nextMeeting.provider]}
            </span>
          </div>
          {data.nextMeeting.meetingLink && (
            <button
              className="btn btn-join"
              onClick={() => onJoinMeeting?.(data.nextMeeting!.meetingLink!)}
            >
              Join Meeting
            </button>
          )}
        </div>
      )}

      <div className="widget-body">
        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : data.upcomingMeetings.length === 0 ? (
          <div className="no-meetings">
            <p>No upcoming meetings</p>
          </div>
        ) : (
          <div className="meetings-list">
            {data.upcomingMeetings.slice(0, 5).map((meeting) => (
              <MeetingListItem
                key={meeting.id}
                meeting={meeting}
                currentTime={currentTime}
                onClick={() => onViewEvent?.(meeting.id)}
              />
            ))}
          </div>
        )}
      </div>

      {onViewAllEvents && (
        <div className="widget-footer">
          <button className="view-all-btn" onClick={onViewAllEvents}>
            View All Events →
          </button>
        </div>
      )}

      <style jsx>{`
        .widget {
          background: white;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .widget-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid #E5E7EB;
        }

        .widget-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #111827;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .refresh-btn {
          width: 28px;
          height: 28px;
          border: none;
          background: #F3F4F6;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          color: #6B7280;
          transition: all 0.2s;
        }

        .refresh-btn:hover:not(:disabled) {
          background: #E5E7EB;
          color: #374151;
        }

        .refresh-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
          display: inline-block;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .widget-stats {
          display: flex;
          padding: 16px 20px;
          gap: 24px;
          background: #FAFAFA;
          border-bottom: 1px solid #E5E7EB;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 700;
          color: #111827;
        }

        .stat-label {
          font-size: 12px;
          color: #6B7280;
          text-transform: uppercase;
        }

        .next-meeting {
          padding: 16px 20px;
          background: #F9FAFB;
          border-bottom: 1px solid #E5E7EB;
        }

        .next-meeting.happening-soon {
          background: #FEF3C7;
          border-left: 4px solid #F59E0B;
        }

        .next-meeting.happening-now {
          background: #DCFCE7;
          border-left: 4px solid #22C55E;
        }

        .next-meeting-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .next-label {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: #6B7280;
        }

        .happening-soon .next-label {
          color: #D97706;
        }

        .happening-now .next-label {
          color: #16A34A;
        }

        .time-until {
          font-size: 12px;
          font-weight: 500;
          color: #6366F1;
          background: #EEF2FF;
          padding: 2px 8px;
          border-radius: 12px;
        }

        .happening-soon .time-until {
          background: #FEF08A;
          color: #A16207;
        }

        .happening-now .time-until {
          background: #BBF7D0;
          color: #166534;
        }

        .next-title {
          font-size: 15px;
          font-weight: 600;
          color: #111827;
          margin: 0 0 8px 0;
        }

        .next-meta {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: #6B7280;
        }

        .dot {
          color: #D1D5DB;
        }

        .provider-icon {
          margin-left: auto;
        }

        .btn-join {
          margin-top: 12px;
          padding: 8px 16px;
          background: #6366F1;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-join:hover {
          background: #4F46E5;
        }

        .widget-body {
          padding: 8px 0;
          min-height: 100px;
        }

        .loading {
          display: flex;
          justify-content: center;
          padding: 32px;
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #E5E7EB;
          border-top-color: #6366F1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .no-meetings {
          text-align: center;
          padding: 24px;
          color: #6B7280;
          font-size: 14px;
        }

        .meetings-list {
          display: flex;
          flex-direction: column;
        }

        .widget-footer {
          padding: 12px 20px;
          border-top: 1px solid #E5E7EB;
        }

        .view-all-btn {
          width: 100%;
          padding: 8px;
          background: transparent;
          border: none;
          color: #6366F1;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: color 0.2s;
        }

        .view-all-btn:hover {
          color: #4F46E5;
        }
      `}</style>
    </div>
  );
}

interface MeetingListItemProps {
  meeting: UpcomingMeeting;
  currentTime: Date;
  onClick?: () => void;
}

function MeetingListItem({ meeting, currentTime, onClick }: MeetingListItemProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const formatDate = (date: Date) => {
    if (isToday(date)) return 'Today';

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
    }).format(date);
  };

  return (
    <button className="meeting-item" onClick={onClick}>
      <div className="meeting-time">
        <span className="time">{formatTime(meeting.startTime)}</span>
        <span className="date">{formatDate(meeting.startTime)}</span>
      </div>
      <div className="meeting-info">
        <span className="meeting-title">{meeting.title}</span>
        <span className="meeting-meta">
          {meeting.attendeesCount} attendee{meeting.attendeesCount !== 1 ? 's' : ''}
          {meeting.hasTranscript && <span className="has-transcript">📝</span>}
        </span>
      </div>
      <span className="provider-icon">{providerIcons[meeting.provider]}</span>

      <style jsx>{`
        .meeting-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 20px;
          background: transparent;
          border: none;
          cursor: pointer;
          transition: background 0.2s;
          text-align: left;
          width: 100%;
        }

        .meeting-item:hover {
          background: #F9FAFB;
        }

        .meeting-time {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          min-width: 60px;
        }

        .time {
          font-size: 13px;
          font-weight: 600;
          color: #111827;
        }

        .date {
          font-size: 11px;
          color: #6B7280;
        }

        .meeting-info {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
        }

        .meeting-title {
          font-size: 14px;
          font-weight: 500;
          color: #111827;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .meeting-meta {
          font-size: 12px;
          color: #6B7280;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .has-transcript {
          margin-left: 4px;
        }

        .provider-icon {
          font-size: 16px;
        }
      `}</style>
    </button>
  );
}

'use client';

/**
 * CalendarEventList Component
 *
 * Displays a filterable, paginated list of calendar events.
 */

import React, { useState, useEffect } from 'react';
import { CalendarEvent, CalendarProvider, CalendarEventListResponse } from './types';
import { CalendarEventCard } from './CalendarEventCard';

interface CalendarEventListProps {
  events?: CalendarEvent[];
  onLoadMore?: () => Promise<void>;
  onLinkTranscript?: (eventId: string) => void;
  onViewTranscript?: (transcriptId: string) => void;
  loading?: boolean;
  hasMore?: boolean;
  emptyMessage?: string;
}

interface FilterState {
  provider?: CalendarProvider;
  hasTranscript?: boolean;
  search: string;
  dateRange: 'today' | 'week' | 'month' | 'all';
}

export function CalendarEventList({
  events = [],
  onLoadMore,
  onLinkTranscript,
  onViewTranscript,
  loading = false,
  hasMore = false,
  emptyMessage = 'No calendar events found',
}: CalendarEventListProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    dateRange: 'week',
  });
  const [filteredEvents, setFilteredEvents] = useState<CalendarEvent[]>(events);

  useEffect(() => {
    let result = [...events];

    // Filter by provider
    if (filters.provider) {
      result = result.filter((e) => e.provider === filters.provider);
    }

    // Filter by transcript status
    if (filters.hasTranscript !== undefined) {
      result = result.filter((e) => e.hasTranscript === filters.hasTranscript);
    }

    // Filter by search
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (e) =>
          e.title.toLowerCase().includes(searchLower) ||
          e.description?.toLowerCase().includes(searchLower) ||
          e.attendees.some(
            (a) =>
              a.email.toLowerCase().includes(searchLower) ||
              a.name?.toLowerCase().includes(searchLower)
          )
      );
    }

    // Filter by date range
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const endOfWeek = new Date(today);
    endOfWeek.setDate(today.getDate() + 7);
    const endOfMonth = new Date(today);
    endOfMonth.setMonth(today.getMonth() + 1);

    if (filters.dateRange === 'today') {
      const tomorrow = new Date(today);
      tomorrow.setDate(today.getDate() + 1);
      result = result.filter(
        (e) => e.startTime >= today && e.startTime < tomorrow
      );
    } else if (filters.dateRange === 'week') {
      result = result.filter(
        (e) => e.startTime >= today && e.startTime < endOfWeek
      );
    } else if (filters.dateRange === 'month') {
      result = result.filter(
        (e) => e.startTime >= today && e.startTime < endOfMonth
      );
    }

    setFilteredEvents(result);
  }, [events, filters]);

  const groupEventsByDate = (events: CalendarEvent[]) => {
    const groups: { [key: string]: CalendarEvent[] } = {};

    events.forEach((event) => {
      const dateKey = event.startTime.toDateString();
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(event);
    });

    return Object.entries(groups).sort(
      ([a], [b]) => new Date(a).getTime() - new Date(b).getTime()
    );
  };

  const formatDateHeader = (dateString: string) => {
    const date = new Date(dateString);
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
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    }).format(date);
  };

  const groupedEvents = groupEventsByDate(filteredEvents);

  return (
    <div className="event-list">
      <div className="filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search events..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
        </div>

        <div className="filter-buttons">
          <select
            value={filters.dateRange}
            onChange={(e) =>
              setFilters({
                ...filters,
                dateRange: e.target.value as FilterState['dateRange'],
              })
            }
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="all">All Time</option>
          </select>

          <select
            value={filters.provider || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                provider: (e.target.value as CalendarProvider) || undefined,
              })
            }
          >
            <option value="">All Calendars</option>
            <option value="google">Google Calendar</option>
            <option value="outlook">Outlook</option>
          </select>

          <select
            value={
              filters.hasTranscript === undefined
                ? ''
                : filters.hasTranscript
                ? 'yes'
                : 'no'
            }
            onChange={(e) =>
              setFilters({
                ...filters,
                hasTranscript:
                  e.target.value === '' ? undefined : e.target.value === 'yes',
              })
            }
          >
            <option value="">All Events</option>
            <option value="yes">With Transcript</option>
            <option value="no">Without Transcript</option>
          </select>
        </div>
      </div>

      {loading && events.length === 0 ? (
        <div className="loading">
          <div className="spinner" />
          <span>Loading events...</span>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📅</span>
          <p>{emptyMessage}</p>
        </div>
      ) : (
        <div className="events-container">
          {groupedEvents.map(([dateKey, dateEvents]) => (
            <div key={dateKey} className="date-group">
              <h3 className="date-header">{formatDateHeader(dateKey)}</h3>
              <div className="events-grid">
                {dateEvents.map((event) => (
                  <CalendarEventCard
                    key={event.id}
                    event={event}
                    onLinkTranscript={onLinkTranscript}
                    onViewTranscript={onViewTranscript}
                  />
                ))}
              </div>
            </div>
          ))}

          {hasMore && (
            <div className="load-more">
              <button
                className="btn btn-secondary"
                onClick={onLoadMore}
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .event-list {
          width: 100%;
        }

        .filters {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 24px;
        }

        .search-box input {
          width: 100%;
          padding: 12px 16px;
          border: 1px solid #E5E7EB;
          border-radius: 8px;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }

        .search-box input:focus {
          border-color: #6366F1;
        }

        .filter-buttons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .filter-buttons select {
          padding: 8px 12px;
          border: 1px solid #E5E7EB;
          border-radius: 6px;
          font-size: 14px;
          background: white;
          cursor: pointer;
          outline: none;
        }

        .filter-buttons select:focus {
          border-color: #6366F1;
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px;
          color: #6B7280;
        }

        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #E5E7EB;
          border-top-color: #6366F1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 12px;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px;
          text-align: center;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .empty-state p {
          color: #6B7280;
          font-size: 16px;
          margin: 0;
        }

        .date-group {
          margin-bottom: 24px;
        }

        .date-header {
          font-size: 14px;
          font-weight: 600;
          color: #6B7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin: 0 0 12px 0;
          padding-bottom: 8px;
          border-bottom: 1px solid #E5E7EB;
        }

        .events-grid {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .load-more {
          display: flex;
          justify-content: center;
          margin-top: 24px;
        }

        .btn {
          padding: 10px 20px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #F3F4F6;
          color: #374151;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #E5E7EB;
        }
      `}</style>
    </div>
  );
}

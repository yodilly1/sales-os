'use client';

import React, { useState, useEffect } from 'react';
import { FollowUp, FollowUpStatus } from './types';

interface ScheduleCalendarProps {
  onSchedule: (followUp: FollowUp, scheduledAt: Date) => void;
  onReschedule?: (followUp: FollowUp, newTime: Date) => void;
  onCancel?: (followUp: FollowUp) => void;
  className?: string;
}

interface ScheduledItem {
  followUp: FollowUp;
  scheduledAt: Date;
}

export function ScheduleCalendar({
  onSchedule,
  onReschedule,
  onCancel,
  className = '',
}: ScheduleCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [scheduledItems, setScheduledItems] = useState<ScheduledItem[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'day' | 'week'>('week');

  useEffect(() => {
    fetchScheduledItems();
  }, [currentDate]);

  async function fetchScheduledItems() {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        status: 'scheduled',
        limit: '100',
      });
      const response = await fetch(`/api/followup?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch scheduled items');

      const data = await response.json();
      const items: ScheduledItem[] = data.items
        .filter((item: FollowUp) => item.scheduledAt)
        .map((item: FollowUp) => ({
          followUp: item,
          scheduledAt: new Date(item.scheduledAt!),
        }));
      setScheduledItems(items);
    } catch (error) {
      console.error('Error fetching scheduled items:', error);
    } finally {
      setLoading(false);
    }
  }

  function getWeekDays(): Date[] {
    const days: Date[] = [];
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }

    return days;
  }

  function getHours(): number[] {
    return Array.from({ length: 12 }, (_, i) => i + 8); // 8am to 7pm
  }

  function navigateWeek(direction: 'prev' | 'next') {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentDate(newDate);
  }

  function navigateDay(direction: 'prev' | 'next') {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + (direction === 'next' ? 1 : -1));
    setCurrentDate(newDate);
  }

  function getItemsForSlot(date: Date, hour: number): ScheduledItem[] {
    return scheduledItems.filter((item) => {
      const itemDate = item.scheduledAt;
      return (
        itemDate.getFullYear() === date.getFullYear() &&
        itemDate.getMonth() === date.getMonth() &&
        itemDate.getDate() === date.getDate() &&
        itemDate.getHours() === hour
      );
    });
  }

  function formatDate(date: Date): string {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  }

  function formatHour(hour: number): string {
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour;
    return `${displayHour}:00 ${ampm}`;
  }

  function isToday(date: Date): boolean {
    const today = new Date();
    return (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    );
  }

  function isWeekend(date: Date): boolean {
    return date.getDay() === 0 || date.getDay() === 6;
  }

  const weekDays = getWeekDays();
  const hours = getHours();

  return (
    <div className={`schedule-calendar ${className}`}>
      {/* Header */}
      <div className="header">
        <div className="nav-controls">
          <button
            onClick={() => view === 'week' ? navigateWeek('prev') : navigateDay('prev')}
            className="nav-btn"
          >
            ←
          </button>
          <button onClick={() => setCurrentDate(new Date())} className="today-btn">
            Today
          </button>
          <button
            onClick={() => view === 'week' ? navigateWeek('next') : navigateDay('next')}
            className="nav-btn"
          >
            →
          </button>
        </div>

        <h2>
          {view === 'week'
            ? `${formatDate(weekDays[0])} - ${formatDate(weekDays[6])}`
            : formatDate(currentDate)}
        </h2>

        <div className="view-toggle">
          <button
            className={view === 'day' ? 'active' : ''}
            onClick={() => setView('day')}
          >
            Day
          </button>
          <button
            className={view === 'week' ? 'active' : ''}
            onClick={() => setView('week')}
          >
            Week
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading schedule...</div>
      ) : (
        <div className="calendar-grid">
          {/* Time column */}
          <div className="time-column">
            <div className="header-cell" />
            {hours.map((hour) => (
              <div key={hour} className="time-cell">
                {formatHour(hour)}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {(view === 'week' ? weekDays : [currentDate]).map((day, dayIndex) => (
            <div
              key={dayIndex}
              className={`day-column ${isToday(day) ? 'today' : ''} ${isWeekend(day) ? 'weekend' : ''}`}
            >
              <div className="header-cell">
                <span className="day-name">
                  {day.toLocaleDateString('en-US', { weekday: 'short' })}
                </span>
                <span className={`day-number ${isToday(day) ? 'today' : ''}`}>
                  {day.getDate()}
                </span>
              </div>

              {hours.map((hour) => {
                const slotItems = getItemsForSlot(day, hour);
                const slotDate = new Date(day);
                slotDate.setHours(hour, 0, 0, 0);

                return (
                  <div
                    key={hour}
                    className={`slot ${selectedSlot?.getTime() === slotDate.getTime() ? 'selected' : ''}`}
                    onClick={() => setSelectedSlot(slotDate)}
                  >
                    {slotItems.map((item) => (
                      <ScheduleItem
                        key={item.followUp.id}
                        item={item}
                        onReschedule={onReschedule}
                        onCancel={onCancel}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="legend">
        <div className="legend-item">
          <span className="legend-color email" />
          <span>Email</span>
        </div>
        <div className="legend-item">
          <span className="legend-color task" />
          <span>Task</span>
        </div>
        <div className="legend-item">
          <span className="legend-color meeting" />
          <span>Meeting</span>
        </div>
      </div>

      <style jsx>{`
        .schedule-calendar {
          display: flex;
          flex-direction: column;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          overflow: hidden;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .nav-controls {
          display: flex;
          gap: 0.5rem;
        }

        .nav-btn,
        .today-btn {
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: #475569;
          background: #f1f5f9;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }

        .nav-btn:hover,
        .today-btn:hover {
          background: #e2e8f0;
        }

        .header h2 {
          margin: 0;
          font-size: 1.125rem;
          font-weight: 600;
        }

        .view-toggle {
          display: flex;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          overflow: hidden;
        }

        .view-toggle button {
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          color: #64748b;
          background: white;
          border: none;
          cursor: pointer;
        }

        .view-toggle button.active {
          color: white;
          background: #3b82f6;
        }

        .loading {
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        .calendar-grid {
          display: flex;
          overflow-x: auto;
        }

        .time-column {
          flex-shrink: 0;
          width: 80px;
          background: #f8fafc;
          border-right: 1px solid #e2e8f0;
        }

        .time-cell {
          height: 60px;
          display: flex;
          align-items: flex-start;
          justify-content: flex-end;
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          color: #64748b;
          border-bottom: 1px solid #f1f5f9;
        }

        .day-column {
          flex: 1;
          min-width: 120px;
          border-right: 1px solid #e2e8f0;
        }

        .day-column:last-child {
          border-right: none;
        }

        .day-column.weekend {
          background: #fafafa;
        }

        .day-column.today {
          background: #eff6ff;
        }

        .header-cell {
          height: 60px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border-bottom: 1px solid #e2e8f0;
          background: #f8fafc;
        }

        .day-name {
          font-size: 0.75rem;
          color: #64748b;
          text-transform: uppercase;
        }

        .day-number {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1e293b;
        }

        .day-number.today {
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          background: #3b82f6;
          border-radius: 9999px;
        }

        .slot {
          height: 60px;
          padding: 0.25rem;
          border-bottom: 1px solid #f1f5f9;
          cursor: pointer;
          transition: background 0.2s;
        }

        .slot:hover {
          background: #f1f5f9;
        }

        .slot.selected {
          background: #dbeafe;
        }

        .legend {
          display: flex;
          gap: 1.5rem;
          padding: 0.75rem 1rem;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.75rem;
          color: #64748b;
        }

        .legend-color {
          width: 0.75rem;
          height: 0.75rem;
          border-radius: 0.25rem;
        }

        .legend-color.email {
          background: #3b82f6;
        }

        .legend-color.task {
          background: #22c55e;
        }

        .legend-color.meeting {
          background: #8b5cf6;
        }
      `}</style>
    </div>
  );
}

interface ScheduleItemProps {
  item: ScheduledItem;
  onReschedule?: (followUp: FollowUp, newTime: Date) => void;
  onCancel?: (followUp: FollowUp) => void;
}

function ScheduleItem({ item, onReschedule, onCancel }: ScheduleItemProps) {
  const { followUp, scheduledAt } = item;

  const typeColors: Record<string, string> = {
    email: '#3b82f6',
    task: '#22c55e',
    content_recommendation: '#f59e0b',
    meeting_suggestion: '#8b5cf6',
  };

  function getTitle(): string {
    switch (followUp.type) {
      case 'email':
        return (followUp as any).draft?.subject || 'Email';
      case 'task':
        return (followUp as any).title || 'Task';
      case 'meeting_suggestion':
        return (followUp as any).suggestion?.title || 'Meeting';
      default:
        return 'Follow-up';
    }
  }

  return (
    <div
      className="schedule-item"
      style={{ borderLeftColor: typeColors[followUp.type] }}
    >
      <span className="item-time">
        {scheduledAt.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
        })}
      </span>
      <span className="item-title">{getTitle()}</span>

      <style jsx>{`
        .schedule-item {
          display: flex;
          flex-direction: column;
          padding: 0.25rem 0.5rem;
          background: white;
          border-left: 3px solid;
          border-radius: 0.25rem;
          font-size: 0.75rem;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .item-time {
          color: #64748b;
        }

        .item-title {
          color: #1e293b;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      `}</style>
    </div>
  );
}

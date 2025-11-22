'use client';

/**
 * LinkTranscriptModal Component
 *
 * Modal for linking a calendar event to a transcript.
 */

import React, { useState, useEffect } from 'react';
import { CalendarEvent } from './types';

interface Transcript {
  id: string;
  title: string;
  recordedAt: Date;
  duration: number;
  participants: string[];
}

interface LinkTranscriptModalProps {
  isOpen: boolean;
  event: CalendarEvent | null;
  onClose: () => void;
  onLink: (eventId: string, transcriptId: string) => Promise<void>;
  onSearchTranscripts: (query: string) => Promise<Transcript[]>;
  suggestedTranscripts?: Transcript[];
}

export function LinkTranscriptModal({
  isOpen,
  event,
  onClose,
  onLink,
  onSearchTranscripts,
  suggestedTranscripts = [],
}: LinkTranscriptModalProps) {
  const [search, setSearch] = useState('');
  const [transcripts, setTranscripts] = useState<Transcript[]>(suggestedTranscripts);
  const [selectedTranscript, setSelectedTranscript] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && suggestedTranscripts.length > 0) {
      setTranscripts(suggestedTranscripts);
    }
  }, [isOpen, suggestedTranscripts]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (search.length >= 2) {
        setLoading(true);
        try {
          const results = await onSearchTranscripts(search);
          setTranscripts(results);
        } catch {
          setTranscripts([]);
        } finally {
          setLoading(false);
        }
      } else if (search.length === 0) {
        setTranscripts(suggestedTranscripts);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [search, onSearchTranscripts, suggestedTranscripts]);

  const handleLink = async () => {
    if (!event || !selectedTranscript) return;

    setLinking(true);
    setError(null);

    try {
      await onLink(event.id, selectedTranscript);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to link transcript. Please try again.'
      );
    } finally {
      setLinking(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  if (!isOpen || !event) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Link Transcript</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="event-preview">
            <span className="preview-label">Meeting</span>
            <h3 className="event-title">{event.title}</h3>
            <span className="event-time">
              {new Intl.DateTimeFormat('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true,
              }).format(event.startTime)}
            </span>
          </div>

          <div className="search-section">
            <label htmlFor="transcript-search">Search Transcripts</label>
            <input
              id="transcript-search"
              type="text"
              placeholder="Search by title or participant..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <div className="transcripts-list">
            {loading ? (
              <div className="loading">
                <div className="spinner" />
                <span>Searching...</span>
              </div>
            ) : transcripts.length === 0 ? (
              <div className="empty-state">
                <p>No transcripts found</p>
              </div>
            ) : (
              transcripts.map((transcript) => (
                <button
                  key={transcript.id}
                  className={`transcript-item ${
                    selectedTranscript === transcript.id ? 'selected' : ''
                  }`}
                  onClick={() => setSelectedTranscript(transcript.id)}
                >
                  <div className="transcript-info">
                    <span className="transcript-title">{transcript.title}</span>
                    <div className="transcript-meta">
                      <span>{formatDate(transcript.recordedAt)}</span>
                      <span className="dot">•</span>
                      <span>{formatDuration(transcript.duration)}</span>
                      <span className="dot">•</span>
                      <span>
                        {transcript.participants.length} participant
                        {transcript.participants.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                  <div className="select-indicator">
                    {selectedTranscript === transcript.id ? '✓' : ''}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleLink}
            disabled={!selectedTranscript || linking}
          >
            {linking ? 'Linking...' : 'Link Transcript'}
          </button>
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: white;
          border-radius: 16px;
          width: 100%;
          max-width: 520px;
          max-height: 80vh;
          display: flex;
          flex-direction: column;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
          overflow: hidden;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 24px;
          border-bottom: 1px solid #E5E7EB;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #111827;
        }

        .close-button {
          width: 32px;
          height: 32px;
          border: none;
          background: #F3F4F6;
          border-radius: 8px;
          font-size: 20px;
          color: #6B7280;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .close-button:hover {
          background: #E5E7EB;
          color: #374151;
        }

        .modal-body {
          padding: 24px;
          overflow-y: auto;
          flex: 1;
        }

        .event-preview {
          padding: 16px;
          background: #F9FAFB;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .preview-label {
          font-size: 11px;
          text-transform: uppercase;
          color: #6B7280;
          font-weight: 500;
        }

        .event-title {
          font-size: 16px;
          font-weight: 600;
          color: #111827;
          margin: 4px 0;
        }

        .event-time {
          font-size: 13px;
          color: #6B7280;
        }

        .search-section {
          margin-bottom: 16px;
        }

        .search-section label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: #374151;
          margin-bottom: 6px;
        }

        .search-section input {
          width: 100%;
          padding: 10px 14px;
          border: 1px solid #E5E7EB;
          border-radius: 8px;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }

        .search-section input:focus {
          border-color: #6366F1;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #FEE2E2;
          border-radius: 8px;
          color: #DC2626;
          font-size: 14px;
          margin-bottom: 16px;
        }

        .transcripts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          max-height: 300px;
          overflow-y: auto;
        }

        .loading,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px;
          color: #6B7280;
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #E5E7EB;
          border-top-color: #6366F1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 8px;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .transcript-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: white;
          border: 2px solid #E5E7EB;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
          width: 100%;
        }

        .transcript-item:hover {
          border-color: #C7D2FE;
          background: #F5F3FF;
        }

        .transcript-item.selected {
          border-color: #6366F1;
          background: #EEF2FF;
        }

        .transcript-info {
          flex: 1;
          min-width: 0;
        }

        .transcript-title {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: #111827;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .transcript-meta {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #6B7280;
          margin-top: 2px;
        }

        .dot {
          color: #D1D5DB;
        }

        .select-indicator {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #6366F1;
          color: white;
          font-size: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 16px 24px;
          border-top: 1px solid #E5E7EB;
          background: #FAFAFA;
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

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: white;
          color: #374151;
          border: 1px solid #E5E7EB;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #F9FAFB;
        }

        .btn-primary {
          background: #6366F1;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #4F46E5;
        }
      `}</style>
    </div>
  );
}

'use client';

/**
 * ConnectCalendarModal Component
 *
 * Modal for connecting calendar providers via OAuth.
 */

import React, { useState } from 'react';
import { CalendarProvider, OAuthURLResponse } from './types';

interface ConnectCalendarModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (provider: CalendarProvider) => Promise<OAuthURLResponse>;
}

interface ProviderOption {
  id: CalendarProvider;
  name: string;
  description: string;
  icon: string;
  color: string;
}

const providers: ProviderOption[] = [
  {
    id: 'google',
    name: 'Google Calendar',
    description: 'Connect your Google Calendar to sync meetings and events',
    icon: '📅',
    color: '#4285F4',
  },
  {
    id: 'outlook',
    name: 'Microsoft Outlook',
    description: 'Connect your Outlook or Microsoft 365 calendar',
    icon: '📆',
    color: '#0078D4',
  },
];

export function ConnectCalendarModal({
  isOpen,
  onClose,
  onConnect,
}: ConnectCalendarModalProps) {
  const [connecting, setConnecting] = useState<CalendarProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async (provider: CalendarProvider) => {
    setConnecting(provider);
    setError(null);

    try {
      const response = await onConnect(provider);
      // Redirect to OAuth authorization URL
      window.location.href = response.authorizationUrl;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to initiate connection. Please try again.'
      );
      setConnecting(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Connect Calendar</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-description">
            Connect your calendar to automatically sync meetings and link them
            with call transcripts.
          </p>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <div className="providers-list">
            {providers.map((provider) => (
              <button
                key={provider.id}
                className="provider-button"
                onClick={() => handleConnect(provider.id)}
                disabled={connecting !== null}
                style={{ '--provider-color': provider.color } as React.CSSProperties}
              >
                <div className="provider-icon">{provider.icon}</div>
                <div className="provider-info">
                  <span className="provider-name">{provider.name}</span>
                  <span className="provider-description">
                    {provider.description}
                  </span>
                </div>
                <div className="provider-action">
                  {connecting === provider.id ? (
                    <span className="connecting">Connecting...</span>
                  ) : (
                    <span className="connect-arrow">→</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <p className="privacy-note">
            We only access your calendar to read meeting information.
            <br />
            Your data is encrypted and never shared.
          </p>
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
          max-width: 480px;
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
        }

        .modal-description {
          color: #6B7280;
          font-size: 14px;
          line-height: 1.5;
          margin: 0 0 20px 0;
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

        .error-icon {
          font-size: 16px;
        }

        .providers-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .provider-button {
          display: flex;
          align-items: center;
          gap: 16px;
          width: 100%;
          padding: 16px;
          background: #FAFAFA;
          border: 2px solid #E5E7EB;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }

        .provider-button:hover:not(:disabled) {
          border-color: var(--provider-color);
          background: white;
        }

        .provider-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .provider-icon {
          font-size: 32px;
        }

        .provider-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .provider-name {
          font-size: 15px;
          font-weight: 600;
          color: #111827;
        }

        .provider-description {
          font-size: 13px;
          color: #6B7280;
        }

        .provider-action {
          display: flex;
          align-items: center;
        }

        .connect-arrow {
          font-size: 20px;
          color: #9CA3AF;
          transition: transform 0.2s;
        }

        .provider-button:hover:not(:disabled) .connect-arrow {
          transform: translateX(4px);
          color: var(--provider-color);
        }

        .connecting {
          font-size: 13px;
          color: #6B7280;
        }

        .modal-footer {
          padding: 16px 24px;
          background: #FAFAFA;
          border-top: 1px solid #E5E7EB;
        }

        .privacy-note {
          font-size: 12px;
          color: #9CA3AF;
          text-align: center;
          margin: 0;
          line-height: 1.5;
        }
      `}</style>
    </div>
  );
}

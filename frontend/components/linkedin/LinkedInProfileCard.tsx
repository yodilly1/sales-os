/**
 * LinkedIn Profile Card Component
 *
 * Displays a LinkedIn profile with key information.
 */

'use client';

import React from 'react';
import type { LinkedInProfile, ConnectionStatus } from '@/lib/api/linkedin';

interface LinkedInProfileCardProps {
  profile: LinkedInProfile;
  onEnrich?: () => void;
  onConnect?: () => void;
  onMessage?: () => void;
  isLoading?: boolean;
  compact?: boolean;
}

const connectionStatusConfig: Record<
  ConnectionStatus,
  { label: string; color: string }
> = {
  not_connected: { label: 'Not Connected', color: 'bg-gray-200 text-gray-700' },
  pending_sent: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
  pending_received: { label: 'Invitation', color: 'bg-blue-100 text-blue-800' },
  connected: { label: 'Connected', color: 'bg-green-100 text-green-800' },
  following: { label: 'Following', color: 'bg-purple-100 text-purple-800' },
};

export function LinkedInProfileCard({
  profile,
  onEnrich,
  onConnect,
  onMessage,
  isLoading,
  compact = false,
}: LinkedInProfileCardProps) {
  const statusConfig = connectionStatusConfig[profile.connection_status];

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {profile.profile_picture_url ? (
            <img
              src={profile.profile_picture_url}
              alt={`${profile.first_name} ${profile.last_name}`}
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-sm">
                {profile.first_name[0]}
                {profile.last_name[0]}
              </span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900 truncate">
              {profile.first_name} {profile.last_name}
            </h4>
            <span
              className={`px-2 py-0.5 text-xs rounded-full ${statusConfig.color}`}
            >
              {statusConfig.label}
            </span>
          </div>
          <p className="text-sm text-gray-600 truncate">{profile.headline}</p>
        </div>

        {/* Action */}
        <a
          href={profile.linkedin_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
        >
          <LinkedInIcon className="w-5 h-5" />
        </a>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Banner */}
      <div
        className="h-24 bg-gradient-to-r from-blue-500 to-blue-600"
        style={
          profile.banner_image_url
            ? { backgroundImage: `url(${profile.banner_image_url})` }
            : undefined
        }
      />

      {/* Profile Header */}
      <div className="px-6 pb-6">
        <div className="flex items-end -mt-12 mb-4">
          {/* Avatar */}
          {profile.profile_picture_url ? (
            <img
              src={profile.profile_picture_url}
              alt={`${profile.first_name} ${profile.last_name}`}
              className="w-24 h-24 rounded-full border-4 border-white object-cover shadow-sm"
            />
          ) : (
            <div className="w-24 h-24 rounded-full border-4 border-white bg-blue-100 flex items-center justify-center shadow-sm">
              <span className="text-blue-600 font-bold text-2xl">
                {profile.first_name[0]}
                {profile.last_name[0]}
              </span>
            </div>
          )}

          {/* Connection Status Badge */}
          <span
            className={`ml-auto px-3 py-1 text-sm rounded-full ${statusConfig.color}`}
          >
            {statusConfig.label}
          </span>
        </div>

        {/* Name and Headline */}
        <h3 className="text-xl font-bold text-gray-900">
          {profile.first_name} {profile.last_name}
        </h3>
        <p className="text-gray-600 mt-1">{profile.headline}</p>

        {/* Current Position */}
        {profile.current_title && profile.current_company && (
          <p className="text-sm text-gray-500 mt-2">
            {profile.current_title} at {profile.current_company}
          </p>
        )}

        {/* Location */}
        {profile.location && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
            <LocationIcon className="w-4 h-4" />
            {profile.location}
            {profile.country && profile.country !== profile.location && (
              <span>, {profile.country}</span>
            )}
          </p>
        )}

        {/* Stats */}
        <div className="flex gap-4 mt-4 text-sm">
          {profile.connections_count !== undefined && (
            <div>
              <span className="font-semibold text-gray-900">
                {formatNumber(profile.connections_count)}
              </span>{' '}
              <span className="text-gray-500">connections</span>
            </div>
          )}
          {profile.followers_count !== undefined && (
            <div>
              <span className="font-semibold text-gray-900">
                {formatNumber(profile.followers_count)}
              </span>{' '}
              <span className="text-gray-500">followers</span>
            </div>
          )}
        </div>

        {/* Badges */}
        <div className="flex gap-2 mt-4">
          {profile.is_open_to_work && (
            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
              Open to Work
            </span>
          )}
          {profile.is_hiring && (
            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
              Hiring
            </span>
          )}
          {profile.is_creator && (
            <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
              Creator
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-6">
          <a
            href={profile.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <LinkedInIcon className="w-4 h-4" />
            View on LinkedIn
          </a>
          {onConnect &&
            profile.connection_status === 'not_connected' && (
              <button
                onClick={onConnect}
                disabled={isLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Connect
              </button>
            )}
          {onMessage && profile.connection_status === 'connected' && (
            <button
              onClick={onMessage}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Message
            </button>
          )}
          {onEnrich && (
            <button
              onClick={onEnrich}
              disabled={isLoading}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              title="Refresh data"
            >
              <RefreshIcon className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Summary */}
        {profile.summary && (
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 mb-2">About</h4>
            <p className="text-sm text-gray-600 whitespace-pre-line line-clamp-4">
              {profile.summary}
            </p>
          </div>
        )}

        {/* Experience */}
        {profile.experiences.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 mb-3">Experience</h4>
            <div className="space-y-4">
              {profile.experiences.slice(0, 3).map((exp, idx) => (
                <div key={idx} className="flex gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded flex-shrink-0 flex items-center justify-center">
                    <BriefcaseIcon className="w-5 h-5 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h5 className="font-medium text-gray-900">{exp.title}</h5>
                    <p className="text-sm text-gray-600">{exp.company_name}</p>
                    {exp.start_date && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(exp.start_date)} -{' '}
                        {exp.is_current ? 'Present' : formatDate(exp.end_date)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills */}
        {profile.skills.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 mb-2">Top Skills</h4>
            <div className="flex flex-wrap gap-2">
              {profile.skills.slice(0, 6).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                >
                  {skill.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        {profile.last_enriched_at && (
          <p className="text-xs text-gray-400 mt-6">
            Data updated: {formatDateTime(profile.last_enriched_at)}
            {profile.enrichment_source && (
              <span> via {profile.enrichment_source}</span>
            )}
          </p>
        )}
      </div>
    </div>
  );
}

// ==================== Helper Functions ====================

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

// ==================== Icons ====================

function LinkedInIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function LocationIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

function RefreshIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

function BriefcaseIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
      />
    </svg>
  );
}

export default LinkedInProfileCard;

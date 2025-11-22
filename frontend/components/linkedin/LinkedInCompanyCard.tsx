/**
 * LinkedIn Company Card Component
 *
 * Displays a LinkedIn company page with key information.
 */

'use client';

import React from 'react';
import type { LinkedInCompany } from '@/lib/api/linkedin';

interface LinkedInCompanyCardProps {
  company: LinkedInCompany;
  onEnrich?: () => void;
  isLoading?: boolean;
  compact?: boolean;
}

export function LinkedInCompanyCard({
  company,
  onEnrich,
  isLoading,
  compact = false,
}: LinkedInCompanyCardProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
        {/* Logo */}
        <div className="flex-shrink-0">
          {company.logo_url ? (
            <img
              src={company.logo_url}
              alt={company.name}
              className="w-10 h-10 rounded object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded bg-blue-100 flex items-center justify-center">
              <BuildingIcon className="w-5 h-5 text-blue-600" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">{company.name}</h4>
          <p className="text-sm text-gray-600 truncate">
            {company.industry}
            {company.employee_count && (
              <span> · {formatNumber(company.employee_count)} employees</span>
            )}
          </p>
        </div>

        {/* Action */}
        <a
          href={company.linkedin_url}
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
      <div className="h-24 bg-gradient-to-r from-blue-600 to-indigo-600" />

      {/* Company Header */}
      <div className="px-6 pb-6">
        <div className="flex items-end -mt-12 mb-4">
          {/* Logo */}
          {company.logo_url ? (
            <img
              src={company.logo_url}
              alt={company.name}
              className="w-20 h-20 rounded-lg border-4 border-white bg-white object-cover shadow-sm"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg border-4 border-white bg-blue-100 flex items-center justify-center shadow-sm">
              <BuildingIcon className="w-10 h-10 text-blue-600" />
            </div>
          )}
        </div>

        {/* Name and Tagline */}
        <h3 className="text-xl font-bold text-gray-900">{company.name}</h3>
        {company.tagline && (
          <p className="text-gray-600 mt-1">{company.tagline}</p>
        )}

        {/* Industry */}
        {company.industry && (
          <p className="text-sm text-gray-500 mt-2">{company.industry}</p>
        )}

        {/* Location */}
        {company.headquarters_location && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
            <LocationIcon className="w-4 h-4" />
            {company.headquarters_location}
          </p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
          {company.employee_count && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(company.employee_count)}
              </div>
              <div className="text-xs text-gray-500">Employees</div>
            </div>
          )}
          {company.followers_count && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {formatNumber(company.followers_count)}
              </div>
              <div className="text-xs text-gray-500">Followers</div>
            </div>
          )}
          {company.founded_year && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-semibold text-gray-900">
                {company.founded_year}
              </div>
              <div className="text-xs text-gray-500">Founded</div>
            </div>
          )}
          {company.company_type && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-semibold text-gray-900">
                {company.company_type}
              </div>
              <div className="text-xs text-gray-500">Type</div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-6">
          <a
            href={company.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <LinkedInIcon className="w-4 h-4" />
            View on LinkedIn
          </a>
          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Website
            </a>
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

        {/* Description */}
        {company.description && (
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 mb-2">About</h4>
            <p className="text-sm text-gray-600 whitespace-pre-line line-clamp-4">
              {company.description}
            </p>
          </div>
        )}

        {/* Specialties */}
        {company.specialties.length > 0 && (
          <div className="mt-6">
            <h4 className="font-semibold text-gray-900 mb-2">Specialties</h4>
            <div className="flex flex-wrap gap-2">
              {company.specialties.map((specialty, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                >
                  {specialty}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        {company.last_enriched_at && (
          <p className="text-xs text-gray-400 mt-6">
            Data updated: {formatDateTime(company.last_enriched_at)}
            {company.enrichment_source && (
              <span> via {company.enrichment_source}</span>
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

function BuildingIcon({ className = 'w-5 h-5' }: { className?: string }) {
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
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  );
}

export default LinkedInCompanyCard;

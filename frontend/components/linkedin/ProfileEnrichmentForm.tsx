/**
 * Profile Enrichment Form Component
 *
 * Form for enriching LinkedIn profiles with various options.
 */

'use client';

import React, { useState } from 'react';
import type { EnrichmentResponse, LinkedInProfile } from '@/lib/api/linkedin';

interface ProfileEnrichmentFormProps {
  onEnrich: (
    linkedinUrl: string,
    options: {
      forceRefresh: boolean;
      includeExperiences: boolean;
      includeEducation: boolean;
      includeSkills: boolean;
    }
  ) => Promise<EnrichmentResponse>;
  onSuccess?: (profile: LinkedInProfile) => void;
}

export function ProfileEnrichmentForm({
  onEnrich,
  onSuccess,
}: ProfileEnrichmentFormProps) {
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [includeExperiences, setIncludeExperiences] = useState(true);
  const [includeEducation, setIncludeEducation] = useState(true);
  const [includeSkills, setIncludeSkills] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnrichmentResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await onEnrich(linkedinUrl, {
        forceRefresh,
        includeExperiences,
        includeEducation,
        includeSkills,
      });

      setResult(response);

      if (response.success && response.profile && onSuccess) {
        onSuccess(response.profile);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to enrich profile');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Enrich LinkedIn Profile
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* LinkedIn URL Input */}
        <div>
          <label
            htmlFor="linkedin-url"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            LinkedIn Profile URL
          </label>
          <input
            id="linkedin-url"
            type="url"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://linkedin.com/in/username"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter a LinkedIn profile URL or just the username
          </p>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">Options</p>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">
              Force refresh (bypass cache)
            </span>
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeExperiences}
              onChange={(e) => setIncludeExperiences(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Include work experience</span>
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeEducation}
              onChange={(e) => setIncludeEducation(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Include education</span>
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeSkills}
              onChange={(e) => setIncludeSkills(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Include skills</span>
          </label>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Success Message */}
        {result?.success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            Profile enriched successfully!
            {result.cached && <span className="ml-1">(from cache)</span>}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !linkedinUrl}
          className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <SpinnerIcon className="w-5 h-5 animate-spin" />
              Enriching...
            </>
          ) : (
            <>
              <SearchIcon className="w-5 h-5" />
              Enrich Profile
            </>
          )}
        </button>
      </form>
    </div>
  );
}

// ==================== Bulk Enrichment Form ====================

interface BulkEnrichmentFormProps {
  onBulkEnrich: (
    linkedinUrls: string[],
    forceRefresh: boolean
  ) => Promise<{
    total_requested: number;
    successful: number;
    failed: number;
  }>;
}

export function BulkEnrichmentForm({ onBulkEnrich }: BulkEnrichmentFormProps) {
  const [urlsText, setUrlsText] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    total_requested: number;
    successful: number;
    failed: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    const urls = urlsText
      .split('\n')
      .map((url) => url.trim())
      .filter((url) => url.length > 0);

    if (urls.length === 0) {
      setError('Please enter at least one LinkedIn URL');
      setIsLoading(false);
      return;
    }

    if (urls.length > 100) {
      setError('Maximum 100 URLs allowed per batch');
      setIsLoading(false);
      return;
    }

    try {
      const response = await onBulkEnrich(urls, forceRefresh);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk enrichment failed');
    } finally {
      setIsLoading(false);
    }
  };

  const urlCount = urlsText
    .split('\n')
    .filter((url) => url.trim().length > 0).length;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Bulk Profile Enrichment
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* URLs Textarea */}
        <div>
          <label
            htmlFor="bulk-urls"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            LinkedIn URLs (one per line)
          </label>
          <textarea
            id="bulk-urls"
            value={urlsText}
            onChange={(e) => setUrlsText(e.target.value)}
            placeholder="https://linkedin.com/in/user1&#10;https://linkedin.com/in/user2&#10;https://linkedin.com/in/user3"
            rows={6}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
          />
          <p className="mt-1 text-xs text-gray-500">
            {urlCount} URL{urlCount !== 1 ? 's' : ''} entered (max 100)
          </p>
        </div>

        {/* Options */}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={forceRefresh}
            onChange={(e) => setForceRefresh(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">
            Force refresh (bypass cache)
          </span>
        </label>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Result Summary */}
        {result && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Results</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-semibold text-gray-900">
                  {result.total_requested}
                </div>
                <div className="text-xs text-gray-500">Total</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-green-600">
                  {result.successful}
                </div>
                <div className="text-xs text-gray-500">Successful</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-red-600">
                  {result.failed}
                </div>
                <div className="text-xs text-gray-500">Failed</div>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || urlCount === 0}
          className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <SpinnerIcon className="w-5 h-5 animate-spin" />
              Processing {urlCount} profiles...
            </>
          ) : (
            <>
              <UsersIcon className="w-5 h-5" />
              Enrich {urlCount} Profile{urlCount !== 1 ? 's' : ''}
            </>
          )}
        </button>
      </form>
    </div>
  );
}

// ==================== Icons ====================

function SearchIcon({ className = 'w-5 h-5' }: { className?: string }) {
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
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  );
}

function SpinnerIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function UsersIcon({ className = 'w-5 h-5' }: { className?: string }) {
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
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

export default ProfileEnrichmentForm;

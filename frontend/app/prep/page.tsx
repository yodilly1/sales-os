"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { MeetingCard } from "./components/MeetingCard";
import { PrepFilters } from "./components/PrepFilters";
import { EmptyState } from "./components/EmptyState";

interface Meeting {
  id: string;
  title: string;
  meeting_type: string;
  scheduled_at: string;
  duration_minutes: string;
  description?: string;
  location?: string;
  meeting_link?: string;
  attendees: Attendee[];
  has_prep_brief: boolean;
  prep_brief_status?: string;
  deal_id?: string;
  company_id?: string;
}

interface Attendee {
  email: string;
  name?: string;
  title?: string;
  role?: string;
}

type FilterPeriod = "today" | "week" | "month" | "all";

export default function PrepPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterPeriod, setFilterPeriod] = useState<FilterPeriod>("week");
  const [generatingBriefs, setGeneratingBriefs] = useState<Set<string>>(
    new Set()
  );

  useEffect(() => {
    fetchMeetings();
  }, [filterPeriod]);

  const fetchMeetings = async () => {
    setLoading(true);
    setError(null);

    try {
      const daysAhead =
        filterPeriod === "today"
          ? 1
          : filterPeriod === "week"
            ? 7
            : filterPeriod === "month"
              ? 30
              : 90;

      const response = await fetch(
        `/api/meetingprep/meetings/upcoming?days_ahead=${daysAhead}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch meetings");
      }

      const data = await response.json();
      setMeetings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const syncCalendar = async (provider: string) => {
    try {
      const response = await fetch("/api/meetingprep/meetings/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          calendar_provider: provider,
          sync_days_ahead: 14,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to sync calendar");
      }

      await fetchMeetings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync calendar");
    }
  };

  const generateBrief = async (meetingId: string) => {
    setGeneratingBriefs((prev) => new Set(prev).add(meetingId));

    try {
      const response = await fetch("/api/meetingprep/briefs/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          meeting_id: meetingId,
          delivery_methods: ["in_app"],
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate brief");
      }

      // Refresh meetings to get updated status
      await fetchMeetings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate brief");
    } finally {
      setGeneratingBriefs((prev) => {
        const next = new Set(prev);
        next.delete(meetingId);
        return next;
      });
    }
  };

  const bulkGenerateBriefs = async () => {
    const meetingsWithoutBriefs = meetings.filter((m) => !m.has_prep_brief);

    if (meetingsWithoutBriefs.length === 0) {
      return;
    }

    try {
      const response = await fetch("/api/meetingprep/briefs/bulk-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          meeting_ids: meetingsWithoutBriefs.map((m) => m.id),
          delivery_methods: ["in_app"],
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate briefs");
      }

      await fetchMeetings();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate briefs"
      );
    }
  };

  const meetingsWithBriefs = meetings.filter((m) => m.has_prep_brief);
  const meetingsWithoutBriefs = meetings.filter((m) => !m.has_prep_brief);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">
                Meeting Prep
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Prepare for your upcoming meetings with AI-generated briefs
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => syncCalendar("google")}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
                </svg>
                Sync Calendar
              </button>
              {meetingsWithoutBriefs.length > 0 && (
                <button
                  onClick={bulkGenerateBriefs}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Generate All Briefs ({meetingsWithoutBriefs.length})
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <PrepFilters
          currentPeriod={filterPeriod}
          onPeriodChange={setFilterPeriod}
        />

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm text-red-700 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : meetings.length === 0 ? (
          <EmptyState onSync={() => syncCalendar("google")} />
        ) : (
          <div className="space-y-8">
            {/* Meetings without briefs */}
            {meetingsWithoutBriefs.length > 0 && (
              <section>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Needs Prep ({meetingsWithoutBriefs.length})
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {meetingsWithoutBriefs.map((meeting) => (
                    <MeetingCard
                      key={meeting.id}
                      meeting={meeting}
                      onGenerateBrief={() => generateBrief(meeting.id)}
                      isGenerating={generatingBriefs.has(meeting.id)}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Meetings with briefs */}
            {meetingsWithBriefs.length > 0 && (
              <section>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Ready to Review ({meetingsWithBriefs.length})
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {meetingsWithBriefs.map((meeting) => (
                    <Link key={meeting.id} href={`/prep/${meeting.id}`}>
                      <MeetingCard meeting={meeting} hasLink />
                    </Link>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

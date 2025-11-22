"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AttendeeCard } from "../components/AttendeeCard";
import { CompanyCard } from "../components/CompanyCard";
import { SPICEDCard } from "../components/SPICEDCard";
import { AgendaSection } from "../components/AgendaSection";
import { QuestionsSection } from "../components/QuestionsSection";
import { ContentRecommendations } from "../components/ContentRecommendations";
import { CallHistorySection } from "../components/CallHistorySection";

interface PrepBrief {
  id: string;
  meeting_id: string;
  status: string;
  generated_at?: string;
  executive_summary?: string;
  attendee_profiles?: AttendeeProfile[];
  company_research?: CompanyResearch;
  call_history?: CallHistoryItem[];
  spiced_context?: SPICEDContext;
  suggested_agenda?: AgendaItem[];
  suggested_questions?: Question[];
  content_recommendations?: ContentRecommendation[];
  email_sent: boolean;
  calendar_attached: boolean;
}

interface AttendeeProfile {
  email: string;
  name?: string;
  title?: string;
  company?: string;
  linkedin_url?: string;
  role?: string;
  background?: string;
  career_highlights?: string[];
  talking_points?: string[];
}

interface CompanyResearch {
  name: string;
  website?: string;
  industry?: string;
  size?: string;
  headquarters?: string;
  description?: string;
  recent_news?: string[];
  key_initiatives?: string[];
  tech_stack?: string[];
  existing_customer?: boolean;
}

interface CallHistoryItem {
  date: string;
  call_type: string;
  attendees: string[];
  summary: string;
  key_outcomes?: string[];
  action_items?: string[];
}

interface SPICEDContext {
  situation?: string;
  pain?: string[];
  impact?: string;
  critical_event?: string;
  decision_process?: string;
  decision_criteria?: string[];
  overall_score?: number;
  gaps?: string[];
}

interface AgendaItem {
  topic: string;
  duration_minutes: number;
  description?: string;
  owner?: string;
  priority: number;
}

interface Question {
  question: string;
  category: string;
  context?: string;
  follow_ups?: string[];
}

interface ContentRecommendation {
  title: string;
  content_type: string;
  relevance: string;
  url?: string;
}

interface Meeting {
  id: string;
  title: string;
  meeting_type: string;
  scheduled_at: string;
  duration_minutes: string;
  description?: string;
  location?: string;
  meeting_link?: string;
}

export default function PrepDetailPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params.id as string;

  const [brief, setBrief] = useState<PrepBrief | null>(null);
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [activeSection, setActiveSection] = useState<string>("summary");

  useEffect(() => {
    fetchData();
  }, [meetingId]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch meeting details
      const meetingResponse = await fetch(
        `/api/meetingprep/meetings/${meetingId}`
      );
      if (!meetingResponse.ok) {
        throw new Error("Meeting not found");
      }
      const meetingData = await meetingResponse.json();
      setMeeting(meetingData);

      // Fetch prep brief
      const briefResponse = await fetch(
        `/api/meetingprep/briefs/${meetingId}`
      );
      if (briefResponse.ok) {
        const briefData = await briefResponse.json();
        setBrief(briefData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const regenerateBrief = async () => {
    setRegenerating(true);

    try {
      const response = await fetch(
        `/api/meetingprep/briefs/${meetingId}/regenerate`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to regenerate brief");
      }

      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to regenerate");
    } finally {
      setRegenerating(false);
    }
  };

  const deliverBrief = async (method: string) => {
    if (!brief) return;

    try {
      await fetch(`/api/meetingprep/briefs/${brief.id}/deliver`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brief_id: brief.id,
          delivery_methods: [method],
        }),
      });

      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deliver brief");
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {error || "Meeting not found"}
          </h2>
          <Link
            href="/prep"
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Back to Meeting Prep
          </Link>
        </div>
      </div>
    );
  }

  const sections = [
    { id: "summary", label: "Summary" },
    { id: "attendees", label: "Attendees" },
    { id: "company", label: "Company" },
    { id: "history", label: "Call History" },
    { id: "spiced", label: "SPICED" },
    { id: "agenda", label: "Agenda" },
    { id: "questions", label: "Questions" },
    { id: "content", label: "Content" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/prep"
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {meeting.title}
                </h1>
                <p className="text-sm text-gray-500">
                  {formatDate(meeting.scheduled_at)} &bull;{" "}
                  {meeting.duration_minutes} min
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {brief && (
                <>
                  <button
                    onClick={() => deliverBrief("email")}
                    disabled={brief.email_sent}
                    className={`inline-flex items-center px-3 py-2 border rounded-md text-sm font-medium ${
                      brief.email_sent
                        ? "border-green-300 text-green-700 bg-green-50"
                        : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                    }`}
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                    {brief.email_sent ? "Email Sent" : "Send Email"}
                  </button>
                  <button
                    onClick={() => deliverBrief("calendar")}
                    disabled={brief.calendar_attached}
                    className={`inline-flex items-center px-3 py-2 border rounded-md text-sm font-medium ${
                      brief.calendar_attached
                        ? "border-green-300 text-green-700 bg-green-50"
                        : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                    }`}
                  >
                    <svg
                      className="w-4 h-4 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    {brief.calendar_attached ? "Attached" : "Add to Calendar"}
                  </button>
                </>
              )}
              <button
                onClick={regenerateBrief}
                disabled={regenerating}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {regenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Regenerating...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4 mr-2"
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
                    Regenerate
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Section Navigation */}
          <nav className="mt-4 -mb-px flex space-x-8 overflow-x-auto">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                  activeSection === section.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {section.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!brief || brief.status !== "completed" ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              {brief?.status === "generating"
                ? "Generating prep brief..."
                : brief?.status === "failed"
                  ? "Brief generation failed"
                  : "No prep brief yet"}
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              {brief?.status === "generating"
                ? "This may take a moment. Please wait..."
                : brief?.status === "failed"
                  ? "Try regenerating the brief."
                  : "Click regenerate to create a prep brief for this meeting."}
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Summary Section */}
            {activeSection === "summary" && brief.executive_summary && (
              <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Executive Summary
                </h2>
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {brief.executive_summary}
                </p>

                {brief.generated_at && (
                  <p className="mt-4 text-xs text-gray-400">
                    Generated {formatDate(brief.generated_at)}
                  </p>
                )}
              </section>
            )}

            {/* Attendees Section */}
            {activeSection === "attendees" && brief.attendee_profiles && (
              <section>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Attendees ({brief.attendee_profiles.length})
                </h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  {brief.attendee_profiles.map((attendee, index) => (
                    <AttendeeCard key={index} attendee={attendee} />
                  ))}
                </div>
              </section>
            )}

            {/* Company Section */}
            {activeSection === "company" && brief.company_research && (
              <CompanyCard company={brief.company_research} />
            )}

            {/* Call History Section */}
            {activeSection === "history" && brief.call_history && (
              <CallHistorySection history={brief.call_history} />
            )}

            {/* SPICED Section */}
            {activeSection === "spiced" && brief.spiced_context && (
              <SPICEDCard spiced={brief.spiced_context} />
            )}

            {/* Agenda Section */}
            {activeSection === "agenda" && brief.suggested_agenda && (
              <AgendaSection
                agenda={brief.suggested_agenda}
                meetingDuration={parseInt(meeting.duration_minutes)}
              />
            )}

            {/* Questions Section */}
            {activeSection === "questions" && brief.suggested_questions && (
              <QuestionsSection questions={brief.suggested_questions} />
            )}

            {/* Content Recommendations Section */}
            {activeSection === "content" && brief.content_recommendations && (
              <ContentRecommendations
                recommendations={brief.content_recommendations}
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

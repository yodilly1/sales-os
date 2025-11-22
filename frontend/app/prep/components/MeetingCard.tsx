"use client";

interface Meeting {
  id: string;
  title: string;
  meeting_type: string;
  scheduled_at: string;
  duration_minutes: string;
  attendees: { email: string; name?: string }[];
  has_prep_brief: boolean;
  prep_brief_status?: string;
}

interface MeetingCardProps {
  meeting: Meeting;
  onGenerateBrief?: () => void;
  isGenerating?: boolean;
  hasLink?: boolean;
}

export function MeetingCard({
  meeting,
  onGenerateBrief,
  isGenerating,
  hasLink,
}: MeetingCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const isTomorrow = date.toDateString() === tomorrow.toDateString();

    if (isToday) {
      return `Today at ${date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`;
    }
    if (isTomorrow) {
      return `Tomorrow at ${date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`;
    }
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const getMeetingTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      discovery: "bg-purple-100 text-purple-800",
      demo: "bg-blue-100 text-blue-800",
      follow_up: "bg-green-100 text-green-800",
      negotiation: "bg-orange-100 text-orange-800",
      qbr: "bg-indigo-100 text-indigo-800",
      renewal: "bg-teal-100 text-teal-800",
      kickoff: "bg-pink-100 text-pink-800",
      check_in: "bg-gray-100 text-gray-800",
    };
    return colors[type] || "bg-gray-100 text-gray-800";
  };

  const formatMeetingType = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 p-4 shadow-sm ${
        hasLink ? "hover:shadow-md hover:border-blue-300 transition-all cursor-pointer" : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-medium text-gray-900 truncate">
            {meeting.title}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {formatDate(meeting.scheduled_at)}
          </p>
        </div>
        <span
          className={`ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getMeetingTypeColor(meeting.meeting_type)}`}
        >
          {formatMeetingType(meeting.meeting_type)}
        </span>
      </div>

      {/* Attendees */}
      {meeting.attendees.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center -space-x-2">
            {meeting.attendees.slice(0, 4).map((attendee, index) => (
              <div
                key={index}
                className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-xs font-medium text-gray-600"
                title={attendee.name || attendee.email}
              >
                {(attendee.name || attendee.email).charAt(0).toUpperCase()}
              </div>
            ))}
            {meeting.attendees.length > 4 && (
              <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-xs font-medium text-gray-500">
                +{meeting.attendees.length - 4}
              </div>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {meeting.attendees.length} attendee
            {meeting.attendees.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <span className="text-xs text-gray-500">
          {meeting.duration_minutes} min
        </span>

        {meeting.has_prep_brief ? (
          <span className="inline-flex items-center text-xs text-green-600">
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Brief Ready
          </span>
        ) : onGenerateBrief ? (
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onGenerateBrief();
            }}
            disabled={isGenerating}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1.5"></div>
                Generating...
              </>
            ) : (
              <>
                <svg
                  className="w-3 h-3 mr-1.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                Generate Brief
              </>
            )}
          </button>
        ) : null}
      </div>
    </div>
  );
}

"use client";

interface CallHistoryItem {
  date: string;
  call_type: string;
  attendees: string[];
  summary: string;
  key_outcomes?: string[];
  action_items?: string[];
}

interface CallHistorySectionProps {
  history: CallHistoryItem[];
}

export function CallHistorySection({ history }: CallHistorySectionProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getCallTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      discovery: "bg-purple-100 text-purple-800",
      demo: "bg-blue-100 text-blue-800",
      follow_up: "bg-green-100 text-green-800",
      negotiation: "bg-orange-100 text-orange-800",
      qbr: "bg-indigo-100 text-indigo-800",
    };
    return colors[type.toLowerCase()] || "bg-gray-100 text-gray-800";
  };

  const formatCallType = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  if (history.length === 0) {
    return (
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
            d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900">
          No previous calls
        </h3>
        <p className="mt-2 text-sm text-gray-500">
          This is the first interaction with these attendees.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Call History</h2>
        <p className="text-sm text-gray-500 mt-1">
          {history.length} previous interaction{history.length !== 1 ? "s" : ""}{" "}
          with attendees
        </p>
      </div>

      {/* Timeline */}
      <div className="px-6 py-5">
        <div className="space-y-6">
          {history.map((call, index) => (
            <div key={index} className="relative">
              {/* Connecting line */}
              {index < history.length - 1 && (
                <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-200 -mb-6"></div>
              )}

              <div className="flex items-start space-x-4">
                {/* Timeline dot */}
                <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-gray-300 flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-4 h-4 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                    />
                  </svg>
                </div>

                {/* Call details */}
                <div className="flex-1 bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCallTypeColor(call.call_type)}`}
                      >
                        {formatCallType(call.call_type)}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatDate(call.date)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400">
                      {call.attendees.length} attendee
                      {call.attendees.length !== 1 ? "s" : ""}
                    </div>
                  </div>

                  <p className="text-sm text-gray-700 mb-3">{call.summary}</p>

                  {/* Key Outcomes */}
                  {call.key_outcomes && call.key_outcomes.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                        Key Outcomes
                      </p>
                      <ul className="space-y-1">
                        {call.key_outcomes.map((outcome, oIndex) => (
                          <li
                            key={oIndex}
                            className="text-sm text-gray-600 flex items-start"
                          >
                            <svg
                              className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                            {outcome}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action Items */}
                  {call.action_items && call.action_items.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                        Action Items
                      </p>
                      <ul className="space-y-1">
                        {call.action_items.map((item, aIndex) => (
                          <li
                            key={aIndex}
                            className="text-sm text-gray-600 flex items-start"
                          >
                            <svg
                              className="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                              />
                            </svg>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Attendees */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs text-gray-400">With:</span>
                      <div className="flex flex-wrap gap-1">
                        {call.attendees.slice(0, 3).map((attendee, aIndex) => (
                          <span
                            key={aIndex}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-200 text-gray-700"
                          >
                            {attendee}
                          </span>
                        ))}
                        {call.attendees.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{call.attendees.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

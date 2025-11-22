"use client";

interface AgendaItem {
  topic: string;
  duration_minutes: number;
  description?: string;
  owner?: string;
  priority: number;
}

interface AgendaSectionProps {
  agenda: AgendaItem[];
  meetingDuration: number;
}

export function AgendaSection({ agenda, meetingDuration }: AgendaSectionProps) {
  const totalPlannedMinutes = agenda.reduce(
    (sum, item) => sum + item.duration_minutes,
    0
  );
  const timeUtilization = Math.round((totalPlannedMinutes / meetingDuration) * 100);

  const getPriorityColor = (priority: number) => {
    if (priority === 1) return "border-l-red-500";
    if (priority === 2) return "border-l-yellow-500";
    return "border-l-gray-300";
  };

  const getPriorityLabel = (priority: number) => {
    if (priority === 1) return "High";
    if (priority === 2) return "Medium";
    return "Low";
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Suggested Agenda
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {agenda.length} items &bull; {totalPlannedMinutes} min planned
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <div
                className={`text-sm font-medium ${
                  timeUtilization > 100
                    ? "text-red-600"
                    : timeUtilization >= 80
                      ? "text-green-600"
                      : "text-yellow-600"
                }`}
              >
                {timeUtilization}% of meeting time
              </div>
            </div>
            {timeUtilization > 100 && (
              <p className="text-xs text-red-500 mt-1">
                Agenda exceeds meeting duration
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="px-6 py-5">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

          {/* Agenda items */}
          <div className="space-y-4">
            {agenda.map((item, index) => {
              // Calculate start time offset
              const previousMinutes = agenda
                .slice(0, index)
                .reduce((sum, i) => sum + i.duration_minutes, 0);

              return (
                <div
                  key={index}
                  className={`relative pl-10 border-l-4 ml-2 -ml-0.5 ${getPriorityColor(item.priority)}`}
                >
                  {/* Timeline dot */}
                  <div className="absolute left-[-7px] top-1 w-3 h-3 bg-white border-2 border-gray-400 rounded-full"></div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {item.topic}
                        </h4>
                        {item.description && (
                          <p className="text-sm text-gray-600 mt-1">
                            {item.description}
                          </p>
                        )}
                      </div>
                      <div className="ml-4 flex-shrink-0 text-right">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {item.duration_minutes} min
                        </span>
                        {item.owner && (
                          <p className="text-xs text-gray-400 mt-1">
                            {item.owner}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Time indicator */}
                    <div className="mt-2 flex items-center text-xs text-gray-400">
                      <svg
                        className="w-3 h-3 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      +{previousMinutes} min
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center space-x-6 text-xs text-gray-500">
          <span className="font-medium">Priority:</span>
          <span className="flex items-center">
            <span className="w-3 h-3 bg-red-500 rounded-sm mr-1"></span>
            High
          </span>
          <span className="flex items-center">
            <span className="w-3 h-3 bg-yellow-500 rounded-sm mr-1"></span>
            Medium
          </span>
          <span className="flex items-center">
            <span className="w-3 h-3 bg-gray-300 rounded-sm mr-1"></span>
            Low
          </span>
        </div>
      </div>
    </div>
  );
}

"use client";

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

interface SPICEDCardProps {
  spiced: SPICEDContext;
}

export function SPICEDCard({ spiced }: SPICEDCardProps) {
  const elements = [
    {
      key: "situation",
      label: "Situation",
      letter: "S",
      color: "bg-blue-500",
      content: spiced.situation,
    },
    {
      key: "pain",
      label: "Pain",
      letter: "P",
      color: "bg-red-500",
      content: spiced.pain?.join(", "),
    },
    {
      key: "impact",
      label: "Impact",
      letter: "I",
      color: "bg-orange-500",
      content: spiced.impact,
    },
    {
      key: "critical_event",
      label: "Critical Event",
      letter: "C",
      color: "bg-yellow-500",
      content: spiced.critical_event,
    },
    {
      key: "decision_process",
      label: "Decision Process",
      letter: "E",
      color: "bg-green-500",
      content: spiced.decision_process,
    },
    {
      key: "decision_criteria",
      label: "Decision Criteria",
      letter: "D",
      color: "bg-purple-500",
      content: spiced.decision_criteria?.join(", "),
    },
  ];

  const hasContent = (element: (typeof elements)[0]) => {
    return element.content && element.content.length > 0;
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-400";
    if (score >= 4) return "text-green-600";
    if (score >= 3) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              SPICED Context
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Key insights from previous interactions
            </p>
          </div>
          {spiced.overall_score !== undefined && (
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Overall Score
              </p>
              <p
                className={`text-2xl font-bold ${getScoreColor(spiced.overall_score)}`}
              >
                {spiced.overall_score.toFixed(1)}
                <span className="text-sm text-gray-400">/5</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* SPICED Elements */}
      <div className="px-6 py-5">
        <div className="space-y-4">
          {elements.map((element) => (
            <div
              key={element.key}
              className={`flex items-start space-x-4 ${!hasContent(element) ? "opacity-50" : ""}`}
            >
              <div
                className={`w-10 h-10 rounded-lg ${element.color} flex items-center justify-center text-white font-bold text-lg flex-shrink-0`}
              >
                {element.letter}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-700">
                  {element.label}
                </h4>
                {hasContent(element) ? (
                  <p className="text-sm text-gray-600 mt-1">{element.content}</p>
                ) : (
                  <p className="text-sm text-gray-400 italic mt-1">
                    Not yet discovered
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gaps Section */}
      {spiced.gaps && spiced.gaps.length > 0 && (
        <div className="px-6 py-4 bg-amber-50 border-t border-amber-100">
          <h4 className="text-sm font-medium text-amber-800 mb-2">
            Gaps to Address
          </h4>
          <ul className="space-y-1">
            {spiced.gaps.map((gap, index) => (
              <li key={index} className="text-sm text-amber-700 flex items-start">
                <svg
                  className="w-4 h-4 text-amber-500 mr-2 mt-0.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

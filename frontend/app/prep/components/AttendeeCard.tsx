"use client";

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

interface AttendeeCardProps {
  attendee: AttendeeProfile;
}

export function AttendeeCard({ attendee }: AttendeeCardProps) {
  const getRoleBadge = (role?: string) => {
    const roleStyles: Record<string, string> = {
      champion: "bg-green-100 text-green-800",
      economic_buyer: "bg-purple-100 text-purple-800",
      technical_buyer: "bg-blue-100 text-blue-800",
      influencer: "bg-yellow-100 text-yellow-800",
      blocker: "bg-red-100 text-red-800",
      end_user: "bg-gray-100 text-gray-800",
    };
    return roleStyles[role || "unknown"] || "bg-gray-100 text-gray-800";
  };

  const formatRole = (role?: string) => {
    if (!role || role === "unknown") return null;
    return role
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold text-lg">
            {(attendee.name || attendee.email).charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="font-medium text-gray-900">
              {attendee.name || attendee.email}
            </h3>
            {attendee.title && (
              <p className="text-sm text-gray-500">{attendee.title}</p>
            )}
            {attendee.company && (
              <p className="text-xs text-gray-400">{attendee.company}</p>
            )}
          </div>
        </div>
        {formatRole(attendee.role) && (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadge(attendee.role)}`}
          >
            {formatRole(attendee.role)}
          </span>
        )}
      </div>

      {/* Background */}
      {attendee.background && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-1">Background</h4>
          <p className="text-sm text-gray-600">{attendee.background}</p>
        </div>
      )}

      {/* Career Highlights */}
      {attendee.career_highlights && attendee.career_highlights.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Career Highlights
          </h4>
          <ul className="space-y-1">
            {attendee.career_highlights.map((highlight, index) => (
              <li
                key={index}
                className="text-sm text-gray-600 flex items-start"
              >
                <span className="text-blue-500 mr-2">•</span>
                {highlight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Talking Points */}
      {attendee.talking_points && attendee.talking_points.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Talking Points
          </h4>
          <ul className="space-y-1">
            {attendee.talking_points.map((point, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="text-green-500 mr-2">→</span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <span className="text-xs text-gray-400">{attendee.email}</span>
        {attendee.linkedin_url && (
          <a
            href={attendee.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
            </svg>
          </a>
        )}
      </div>
    </div>
  );
}

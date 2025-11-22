'use client';

import { Team } from '@/types';
import { Badge } from '@/components/ui/Badge';
import Link from 'next/link';

interface TeamListProps {
  teams: Team[];
  onEdit?: (team: Team) => void;
  onDelete?: (team: Team) => void;
}

export function TeamList({ teams, onEdit, onDelete }: TeamListProps) {
  if (teams.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No teams</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by creating a new team.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden rounded-md">
      <ul className="divide-y divide-gray-200">
        {teams.map((team) => (
          <li key={team.id}>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/team/${team.id}`}
                    className="text-sm font-medium text-primary-600 hover:text-primary-800 truncate"
                  >
                    {team.name}
                  </Link>
                  <p className="mt-1 text-sm text-gray-500 truncate">
                    {team.description || 'No description'}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-sm text-gray-500">
                    {team.member_count} member{team.member_count !== 1 ? 's' : ''}
                  </div>
                  <Badge variant={team.is_active ? 'success' : 'error'}>
                    {team.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {(onEdit || onDelete) && (
                    <div className="flex gap-2">
                      {onEdit && (
                        <button
                          onClick={() => onEdit(team)}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Edit
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={() => onDelete(team)}
                          className="text-sm text-red-500 hover:text-red-700"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

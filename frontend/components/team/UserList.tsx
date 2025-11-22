'use client';

import { User, UserRole } from '@/types';
import { Badge } from '@/components/ui/Badge';

interface UserListProps {
  users: User[];
  onEdit?: (user: User) => void;
  onDeactivate?: (user: User) => void;
  onReactivate?: (user: User) => void;
  currentUserId?: string;
}

const roleLabels: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Admin',
  [UserRole.MANAGER]: 'Manager',
  [UserRole.REP]: 'Sales Rep',
};

const roleBadgeVariants: Record<UserRole, 'info' | 'warning' | 'default'> = {
  [UserRole.ADMIN]: 'info',
  [UserRole.MANAGER]: 'warning',
  [UserRole.REP]: 'default',
};

export function UserList({
  users,
  onEdit,
  onDeactivate,
  onReactivate,
  currentUserId,
}: UserListProps) {
  if (users.length === 0) {
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
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No users</h3>
        <p className="mt-1 text-sm text-gray-500">
          Invite team members to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden rounded-md">
      <ul className="divide-y divide-gray-200">
        {users.map((user) => (
          <li key={user.id}>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center min-w-0">
                  <div className="flex-shrink-0">
                    {user.avatar_url ? (
                      <img
                        className="h-10 w-10 rounded-full"
                        src={user.avatar_url}
                        alt=""
                      />
                    ) : (
                      <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                        <span className="text-primary-700 font-medium">
                          {user.full_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="ml-4 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user.full_name}
                      {user.id === currentUserId && (
                        <span className="ml-2 text-xs text-gray-500">(you)</span>
                      )}
                    </p>
                    <p className="text-sm text-gray-500 truncate">{user.email}</p>
                    {user.title && (
                      <p className="text-xs text-gray-400">{user.title}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={roleBadgeVariants[user.role as UserRole]}>
                    {roleLabels[user.role as UserRole] || user.role}
                  </Badge>
                  <Badge variant={user.is_active ? 'success' : 'error'} size="sm">
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {user.id !== currentUserId && (
                    <div className="flex gap-2">
                      {onEdit && (
                        <button
                          onClick={() => onEdit(user)}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Edit
                        </button>
                      )}
                      {user.is_active && onDeactivate && (
                        <button
                          onClick={() => onDeactivate(user)}
                          className="text-sm text-red-500 hover:text-red-700"
                        >
                          Deactivate
                        </button>
                      )}
                      {!user.is_active && onReactivate && (
                        <button
                          onClick={() => onReactivate(user)}
                          className="text-sm text-green-500 hover:text-green-700"
                        >
                          Reactivate
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

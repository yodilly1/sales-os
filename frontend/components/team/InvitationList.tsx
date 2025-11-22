'use client';

import { Invitation, InvitationStatus, UserRole } from '@/types';
import { Badge } from '@/components/ui/Badge';
import { format } from 'date-fns';

interface InvitationListProps {
  invitations: Invitation[];
  onResend?: (invitation: Invitation) => void;
  onRevoke?: (invitation: Invitation) => void;
}

const statusBadgeVariants: Record<InvitationStatus, 'warning' | 'success' | 'error' | 'default'> = {
  [InvitationStatus.PENDING]: 'warning',
  [InvitationStatus.ACCEPTED]: 'success',
  [InvitationStatus.EXPIRED]: 'error',
  [InvitationStatus.REVOKED]: 'default',
};

const roleLabels: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Admin',
  [UserRole.MANAGER]: 'Manager',
  [UserRole.REP]: 'Sales Rep',
};

export function InvitationList({ invitations, onResend, onRevoke }: InvitationListProps) {
  if (invitations.length === 0) {
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
            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No invitations</h3>
        <p className="mt-1 text-sm text-gray-500">
          Invite new members to your organization.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden rounded-md">
      <ul className="divide-y divide-gray-200">
        {invitations.map((invitation) => (
          <li key={invitation.id}>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {invitation.email}
                  </p>
                  <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                    <span>Role: {roleLabels[invitation.role] || invitation.role}</span>
                    <span>|</span>
                    <span>
                      Invited by {invitation.invited_by_name || invitation.invited_by_email || 'Unknown'}
                    </span>
                    <span>|</span>
                    <span>
                      Expires: {format(new Date(invitation.expires_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={statusBadgeVariants[invitation.status as InvitationStatus]}>
                    {invitation.status.charAt(0).toUpperCase() + invitation.status.slice(1)}
                  </Badge>
                  {invitation.status === InvitationStatus.PENDING && (
                    <div className="flex gap-2">
                      {onResend && (
                        <button
                          onClick={() => onResend(invitation)}
                          className="text-sm text-primary-600 hover:text-primary-800"
                        >
                          Resend
                        </button>
                      )}
                      {onRevoke && (
                        <button
                          onClick={() => onRevoke(invitation)}
                          className="text-sm text-red-500 hover:text-red-700"
                        >
                          Revoke
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

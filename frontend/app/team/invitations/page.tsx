'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { InvitationList } from '@/components/team/InvitationList';
import { InviteUserForm } from '@/components/team/InviteUserForm';
import { api } from '@/lib/api';
import type { Invitation, Team, InviteUserForm as InviteUserFormData } from '@/types';

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);

  useEffect(() => {
    api.loadTokenFromStorage();
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [invitationsResponse, teamsResponse] = await Promise.all([
        api.listInvitations(),
        api.listTeams(),
      ]);
      setInvitations(invitationsResponse.items);
      setTeams(teamsResponse.items);
    } catch (err) {
      setError('Failed to load invitations');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInviteUser = async (data: InviteUserFormData) => {
    await api.createInvitation(data);
    setIsInviteModalOpen(false);
    fetchData();
  };

  const handleResendInvitation = async (invitation: Invitation) => {
    try {
      await api.resendInvitation(invitation.id);
      fetchData();
    } catch (err) {
      console.error('Failed to resend invitation:', err);
    }
  };

  const handleRevokeInvitation = async (invitation: Invitation) => {
    if (
      window.confirm(
        `Are you sure you want to revoke the invitation for "${invitation.email}"?`
      )
    ) {
      try {
        await api.revokeInvitation(invitation.id);
        fetchData();
      } catch (err) {
        console.error('Failed to revoke invitation:', err);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Invitations</h2>
          <p className="text-sm text-gray-500">
            Track and manage pending invitations
          </p>
        </div>
        <Button onClick={() => setIsInviteModalOpen(true)}>
          Send Invitation
        </Button>
      </div>

      <InvitationList
        invitations={invitations}
        onResend={handleResendInvitation}
        onRevoke={handleRevokeInvitation}
      />

      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title="Invite New User"
      >
        <InviteUserForm
          teams={teams}
          onSubmit={handleInviteUser}
          onCancel={() => setIsInviteModalOpen(false)}
        />
      </Modal>
    </div>
  );
}

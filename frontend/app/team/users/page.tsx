'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { UserList } from '@/components/team/UserList';
import { InviteUserForm } from '@/components/team/InviteUserForm';
import { api } from '@/lib/api';
import type { User, Team, InviteUserForm as InviteUserFormData } from '@/types';

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
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
      const [usersResponse, teamsResponse, user] = await Promise.all([
        api.listUsers(1, 100, false), // Include inactive users
        api.listTeams(),
        api.getCurrentUser(),
      ]);
      setUsers(usersResponse.items);
      setTeams(teamsResponse.items);
      setCurrentUser(user);
    } catch (err) {
      setError('Failed to load users');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInviteUser = async (data: InviteUserFormData) => {
    await api.createInvitation(data);
    setIsInviteModalOpen(false);
    // Optionally show a success message
  };

  const handleDeactivateUser = async (user: User) => {
    if (
      window.confirm(
        `Are you sure you want to deactivate "${user.full_name}"? They will no longer be able to access the system.`
      )
    ) {
      try {
        await api.deactivateUser(user.id);
        fetchData();
      } catch (err) {
        console.error('Failed to deactivate user:', err);
      }
    }
  };

  const handleReactivateUser = async (user: User) => {
    try {
      await api.reactivateUser(user.id);
      fetchData();
    } catch (err) {
      console.error('Failed to reactivate user:', err);
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
          <h2 className="text-lg font-medium text-gray-900">Users</h2>
          <p className="text-sm text-gray-500">
            Manage users in your organization
          </p>
        </div>
        <Button onClick={() => setIsInviteModalOpen(true)}>Invite User</Button>
      </div>

      <UserList
        users={users}
        currentUserId={currentUser?.id}
        onDeactivate={handleDeactivateUser}
        onReactivate={handleReactivateUser}
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

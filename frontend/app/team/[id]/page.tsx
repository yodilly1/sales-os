'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { api } from '@/lib/api';
import type { TeamWithMembers, User, TeamMember } from '@/types';

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.id as string;

  const [team, setTeam] = useState<TeamWithMembers | null>(null);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [isTeamLead, setIsTeamLead] = useState(false);

  useEffect(() => {
    api.loadTokenFromStorage();
    fetchData();
  }, [teamId]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [teamData, usersResponse] = await Promise.all([
        api.getTeam(teamId),
        api.listUsers(1, 100),
      ]);
      setTeam(teamData);
      setAllUsers(usersResponse.items);
    } catch (err) {
      setError('Failed to load team');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMember = async () => {
    if (!selectedUserId) return;

    try {
      await api.addTeamMember(teamId, selectedUserId, isTeamLead);
      setIsAddMemberModalOpen(false);
      setSelectedUserId('');
      setIsTeamLead(false);
      fetchData();
    } catch (err) {
      console.error('Failed to add member:', err);
    }
  };

  const handleRemoveMember = async (member: TeamMember) => {
    if (
      window.confirm(
        `Are you sure you want to remove "${member.user_name}" from this team?`
      )
    ) {
      try {
        await api.removeTeamMember(teamId, member.user_id);
        fetchData();
      } catch (err) {
        console.error('Failed to remove member:', err);
      }
    }
  };

  const handleToggleTeamLead = async (member: TeamMember) => {
    try {
      await api.updateTeamMember(teamId, member.user_id, {
        is_team_lead: !member.is_team_lead,
      });
      fetchData();
    } catch (err) {
      console.error('Failed to update member:', err);
    }
  };

  // Get users not already in team
  const availableUsers = allUsers.filter(
    (user) => !team?.members.some((m) => m.user_id === user.id)
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || 'Team not found'}
      </div>
    );
  }

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm">
        <Link href="/team" className="text-primary-600 hover:text-primary-800">
          Teams
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-500">{team.name}</span>
      </nav>

      {/* Team Header */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{team.name}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {team.description || 'No description'}
            </p>
            <div className="mt-3 flex items-center gap-3">
              <Badge variant={team.is_active ? 'success' : 'error'}>
                {team.is_active ? 'Active' : 'Inactive'}
              </Badge>
              <span className="text-sm text-gray-500">
                {team.member_count} member{team.member_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
          <Button onClick={() => setIsAddMemberModalOpen(true)}>
            Add Member
          </Button>
        </div>
      </div>

      {/* Team Members */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Team Members</h3>
        </div>
        {team.members.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No members in this team yet. Add members to get started.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {team.members.map((member) => (
              <li key={member.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <span className="text-primary-700 font-medium">
                        {member.user_name?.charAt(0).toUpperCase() || '?'}
                      </span>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-900">
                        {member.user_name}
                      </p>
                      <p className="text-sm text-gray-500">{member.user_email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {member.is_team_lead && (
                      <Badge variant="info">Team Lead</Badge>
                    )}
                    <button
                      onClick={() => handleToggleTeamLead(member)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      {member.is_team_lead ? 'Remove as Lead' : 'Make Lead'}
                    </button>
                    <button
                      onClick={() => handleRemoveMember(member)}
                      className="text-sm text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add Member Modal */}
      <Modal
        isOpen={isAddMemberModalOpen}
        onClose={() => setIsAddMemberModalOpen(false)}
        title="Add Team Member"
      >
        <div className="space-y-4">
          {availableUsers.length === 0 ? (
            <p className="text-gray-500">
              All users are already members of this team.
            </p>
          ) : (
            <>
              <Select
                id="user"
                label="Select User"
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                options={[
                  { value: '', label: 'Choose a user...' },
                  ...availableUsers.map((u) => ({
                    value: u.id,
                    label: `${u.full_name} (${u.email})`,
                  })),
                ]}
              />

              <div className="flex items-center">
                <input
                  id="team_lead"
                  type="checkbox"
                  checked={isTeamLead}
                  onChange={(e) => setIsTeamLead(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <label
                  htmlFor="team_lead"
                  className="ml-2 text-sm text-gray-700"
                >
                  Make team lead
                </label>
              </div>
            </>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setIsAddMemberModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddMember}
              disabled={!selectedUserId || availableUsers.length === 0}
            >
              Add Member
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

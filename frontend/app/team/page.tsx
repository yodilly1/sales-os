'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { TeamList } from '@/components/team/TeamList';
import { CreateTeamForm } from '@/components/team/CreateTeamForm';
import { api } from '@/lib/api';
import type { Team, CreateTeamForm as CreateTeamFormData } from '@/types';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    api.loadTokenFromStorage();
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      setIsLoading(true);
      const response = await api.listTeams();
      setTeams(response.items);
    } catch (err) {
      setError('Failed to load teams');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTeam = async (data: CreateTeamFormData) => {
    await api.createTeam(data);
    setIsCreateModalOpen(false);
    fetchTeams();
  };

  const handleEditTeam = (team: Team) => {
    // Navigate to team detail page for editing
    window.location.href = `/team/${team.id}`;
  };

  const handleDeleteTeam = async (team: Team) => {
    if (window.confirm(`Are you sure you want to delete "${team.name}"?`)) {
      try {
        await api.deleteTeam(team.id);
        fetchTeams();
      } catch (err) {
        console.error('Failed to delete team:', err);
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
          <h2 className="text-lg font-medium text-gray-900">Teams</h2>
          <p className="text-sm text-gray-500">
            Organize your sales team into groups
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create Team</Button>
      </div>

      <TeamList
        teams={teams}
        onEdit={handleEditTeam}
        onDelete={handleDeleteTeam}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Team"
      >
        <CreateTeamForm
          onSubmit={handleCreateTeam}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>
    </div>
  );
}

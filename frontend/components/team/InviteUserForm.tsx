'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { UserRole, Team, InviteUserForm as InviteUserFormData } from '@/types';

interface InviteUserFormProps {
  teams: Team[];
  onSubmit: (data: InviteUserFormData) => Promise<void>;
  onCancel: () => void;
}

export function InviteUserForm({ teams, onSubmit, onCancel }: InviteUserFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<InviteUserFormData>({
    email: '',
    role: UserRole.REP,
    team_id: undefined,
    message: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await onSubmit(formData);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send invitation';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const roleOptions = [
    { value: UserRole.REP, label: 'Sales Rep' },
    { value: UserRole.MANAGER, label: 'Manager' },
    { value: UserRole.ADMIN, label: 'Admin' },
  ];

  const teamOptions = [
    { value: '', label: 'No team (assign later)' },
    ...teams.map((t) => ({ value: t.id, label: t.name })),
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <Input
        id="email"
        type="email"
        label="Email Address"
        value={formData.email}
        onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
        placeholder="colleague@company.com"
        required
      />

      <Select
        id="role"
        label="Role"
        value={formData.role}
        onChange={(e) =>
          setFormData((prev) => ({ ...prev, role: e.target.value as UserRole }))
        }
        options={roleOptions}
      />

      <Select
        id="team"
        label="Assign to Team"
        value={formData.team_id || ''}
        onChange={(e) =>
          setFormData((prev) => ({
            ...prev,
            team_id: e.target.value || undefined,
          }))
        }
        options={teamOptions}
      />

      <div>
        <label htmlFor="message" className="label">
          Personal Message (optional)
        </label>
        <textarea
          id="message"
          className="input min-h-[80px]"
          value={formData.message}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, message: e.target.value }))
          }
          placeholder="Add a personal note to the invitation email..."
          maxLength={500}
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isLoading}>
          Send Invitation
        </Button>
      </div>
    </form>
  );
}

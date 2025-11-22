'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { CreateTeamForm as CreateTeamFormData } from '@/types';

interface CreateTeamFormProps {
  onSubmit: (data: CreateTeamFormData) => Promise<void>;
  onCancel: () => void;
}

export function CreateTeamForm({ onSubmit, onCancel }: CreateTeamFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateTeamFormData>({
    name: '',
    slug: '',
    description: '',
  });

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value;
    setFormData((prev) => ({
      ...prev,
      name,
      slug: generateSlug(name),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await onSubmit(formData);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create team';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <Input
        id="name"
        label="Team Name"
        value={formData.name}
        onChange={handleNameChange}
        placeholder="e.g., Enterprise Sales"
        required
      />

      <Input
        id="slug"
        label="Team Slug"
        value={formData.slug}
        onChange={(e) => setFormData((prev) => ({ ...prev, slug: e.target.value }))}
        placeholder="e.g., enterprise-sales"
        pattern="^[a-z0-9-]+$"
        title="Only lowercase letters, numbers, and hyphens allowed"
        required
      />

      <div>
        <label htmlFor="description" className="label">
          Description (optional)
        </label>
        <textarea
          id="description"
          className="input min-h-[80px]"
          value={formData.description}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, description: e.target.value }))
          }
          placeholder="What does this team do?"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isLoading}>
          Create Team
        </Button>
      </div>
    </form>
  );
}

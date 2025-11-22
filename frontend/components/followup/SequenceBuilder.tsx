'use client';

import React, { useState } from 'react';
import { Sequence, SequenceStep, SequenceStepType, ApprovalMode } from './types';

interface SequenceBuilderProps {
  initialSequence?: Partial<Sequence>;
  templates?: Record<string, { name: string; description: string; steps: Partial<SequenceStep>[] }>;
  onSave: (sequence: Partial<Sequence>) => void;
  onCancel?: () => void;
}

const stepTypeIcons: Record<SequenceStepType, string> = {
  email: '📧',
  task: '✅',
  wait: '⏰',
  condition: '🔀',
};

const stepTypeLabels: Record<SequenceStepType, string> = {
  email: 'Send Email',
  task: 'Create Task',
  wait: 'Wait',
  condition: 'Condition',
};

export function SequenceBuilder({
  initialSequence,
  templates,
  onSave,
  onCancel,
}: SequenceBuilderProps) {
  const [name, setName] = useState(initialSequence?.name || '');
  const [description, setDescription] = useState(initialSequence?.description || '');
  const [steps, setSteps] = useState<Partial<SequenceStep>[]>(initialSequence?.steps || []);
  const [approvalMode, setApprovalMode] = useState<ApprovalMode>(
    initialSequence?.approvalMode || 'manual'
  );
  const [stopOnReply, setStopOnReply] = useState(initialSequence?.stopOnReply ?? true);
  const [businessHoursOnly, setBusinessHoursOnly] = useState(
    initialSequence?.businessHoursOnly ?? true
  );

  function addStep(type: SequenceStepType) {
    const newStep: Partial<SequenceStep> = {
      stepNumber: steps.length + 1,
      stepType: type,
      delayHours: type === 'wait' ? 24 : 0,
      status: 'draft',
    };
    setSteps([...steps, newStep]);
  }

  function updateStep(index: number, updates: Partial<SequenceStep>) {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], ...updates };
    setSteps(newSteps);
  }

  function removeStep(index: number) {
    const newSteps = steps.filter((_, i) => i !== index);
    // Renumber steps
    newSteps.forEach((step, i) => {
      step.stepNumber = i + 1;
    });
    setSteps(newSteps);
  }

  function moveStep(index: number, direction: 'up' | 'down') {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= steps.length) return;

    const newSteps = [...steps];
    [newSteps[index], newSteps[newIndex]] = [newSteps[newIndex], newSteps[index]];
    // Renumber steps
    newSteps.forEach((step, i) => {
      step.stepNumber = i + 1;
    });
    setSteps(newSteps);
  }

  function loadTemplate(templateKey: string) {
    const template = templates?.[templateKey];
    if (template) {
      setName(template.name);
      setDescription(template.description);
      setSteps(template.steps.map((step, index) => ({
        ...step,
        stepNumber: index + 1,
        status: 'draft' as const,
      })));
    }
  }

  function handleSave() {
    onSave({
      name,
      description,
      steps: steps as SequenceStep[],
      totalSteps: steps.length,
      approvalMode,
      stopOnReply,
      businessHoursOnly,
    });
  }

  const isValid = name.trim() && steps.length > 0;

  return (
    <div className="sequence-builder">
      {/* Header */}
      <div className="header">
        <h2>Build Sequence</h2>

        {templates && Object.keys(templates).length > 0 && (
          <div className="templates">
            <select
              onChange={(e) => e.target.value && loadTemplate(e.target.value)}
              defaultValue=""
            >
              <option value="">Load from template...</option>
              {Object.entries(templates).map(([key, template]) => (
                <option key={key} value={key}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Basic info */}
      <div className="basic-info">
        <div className="form-group">
          <label htmlFor="sequence-name">Sequence Name</label>
          <input
            id="sequence-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Post-Demo Follow-up"
          />
        </div>

        <div className="form-group">
          <label htmlFor="sequence-description">Description (optional)</label>
          <textarea
            id="sequence-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the purpose of this sequence..."
            rows={2}
          />
        </div>
      </div>

      {/* Settings */}
      <div className="settings">
        <h3>Settings</h3>
        <div className="settings-grid">
          <label className="setting-item">
            <span>Approval Mode</span>
            <select
              value={approvalMode}
              onChange={(e) => setApprovalMode(e.target.value as ApprovalMode)}
            >
              <option value="manual">Manual - Review each step</option>
              <option value="auto">Auto - Send automatically</option>
            </select>
          </label>

          <label className="setting-item checkbox">
            <input
              type="checkbox"
              checked={stopOnReply}
              onChange={(e) => setStopOnReply(e.target.checked)}
            />
            <span>Stop sequence when prospect replies</span>
          </label>

          <label className="setting-item checkbox">
            <input
              type="checkbox"
              checked={businessHoursOnly}
              onChange={(e) => setBusinessHoursOnly(e.target.checked)}
            />
            <span>Only send during business hours</span>
          </label>
        </div>
      </div>

      {/* Steps */}
      <div className="steps-section">
        <h3>Steps ({steps.length})</h3>

        {steps.length === 0 ? (
          <div className="empty-steps">
            <p>No steps added yet. Add your first step to get started.</p>
          </div>
        ) : (
          <div className="steps-list">
            {steps.map((step, index) => (
              <StepEditor
                key={index}
                step={step}
                index={index}
                totalSteps={steps.length}
                onUpdate={(updates) => updateStep(index, updates)}
                onRemove={() => removeStep(index)}
                onMoveUp={() => moveStep(index, 'up')}
                onMoveDown={() => moveStep(index, 'down')}
              />
            ))}
          </div>
        )}

        {/* Add step buttons */}
        <div className="add-step">
          <span>Add step:</span>
          {(['email', 'task', 'wait', 'condition'] as SequenceStepType[]).map((type) => (
            <button
              key={type}
              onClick={() => addStep(type)}
              className="add-step-btn"
            >
              {stepTypeIcons[type]} {stepTypeLabels[type]}
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="actions">
        <button
          onClick={handleSave}
          disabled={!isValid}
          className="btn-save"
        >
          Save Sequence
        </button>
        {onCancel && (
          <button onClick={onCancel} className="btn-cancel">
            Cancel
          </button>
        )}
      </div>

      <style jsx>{`
        .sequence-builder {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 1.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header h2 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .templates select {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
        }

        .basic-info {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-size: 0.875rem;
          font-weight: 500;
          color: #475569;
        }

        .form-group input,
        .form-group textarea {
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          font-size: 0.875rem;
        }

        .settings h3,
        .steps-section h3 {
          margin: 0 0 0.75rem 0;
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
        }

        .settings-grid {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .setting-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .setting-item span {
          font-size: 0.875rem;
          color: #475569;
        }

        .setting-item select {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
        }

        .setting-item.checkbox {
          cursor: pointer;
        }

        .setting-item.checkbox input {
          width: 1rem;
          height: 1rem;
        }

        .empty-steps {
          padding: 2rem;
          text-align: center;
          color: #64748b;
          background: #f8fafc;
          border: 2px dashed #e2e8f0;
          border-radius: 0.5rem;
        }

        .steps-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .add-step {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .add-step span {
          font-size: 0.875rem;
          color: #64748b;
        }

        .add-step-btn {
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: #475569;
          background: #f1f5f9;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .add-step-btn:hover {
          background: #e2e8f0;
        }

        .actions {
          display: flex;
          gap: 0.75rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .btn-save {
          padding: 0.75rem 1.5rem;
          font-weight: 500;
          color: white;
          background: #3b82f6;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }

        .btn-save:disabled {
          background: #94a3b8;
          cursor: not-allowed;
        }

        .btn-cancel {
          padding: 0.75rem 1.5rem;
          font-weight: 500;
          color: #475569;
          background: #f1f5f9;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}

interface StepEditorProps {
  step: Partial<SequenceStep>;
  index: number;
  totalSteps: number;
  onUpdate: (updates: Partial<SequenceStep>) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

function StepEditor({
  step,
  index,
  totalSteps,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
}: StepEditorProps) {
  return (
    <div className="step-editor">
      <div className="step-header">
        <span className="step-number">{step.stepNumber}</span>
        <span className="step-icon">{stepTypeIcons[step.stepType!]}</span>
        <span className="step-type">{stepTypeLabels[step.stepType!]}</span>

        <div className="step-controls">
          <button
            onClick={onMoveUp}
            disabled={index === 0}
            className="control-btn"
            title="Move up"
          >
            ↑
          </button>
          <button
            onClick={onMoveDown}
            disabled={index === totalSteps - 1}
            className="control-btn"
            title="Move down"
          >
            ↓
          </button>
          <button
            onClick={onRemove}
            className="control-btn remove"
            title="Remove step"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="step-content">
        {step.stepType === 'wait' && (
          <div className="wait-config">
            <label>Wait for</label>
            <input
              type="number"
              value={step.delayHours || 24}
              onChange={(e) => onUpdate({ delayHours: parseInt(e.target.value) || 0 })}
              min={0}
            />
            <span>hours before next step</span>
          </div>
        )}

        {step.stepType === 'email' && (
          <div className="email-config">
            <label>Email template (optional)</label>
            <input
              type="text"
              placeholder="Enter template ID or leave blank for custom"
              value={step.emailTemplateId || ''}
              onChange={(e) => onUpdate({ emailTemplateId: e.target.value || undefined })}
            />
          </div>
        )}

        {step.stepType === 'task' && (
          <div className="task-config">
            <label>Task description</label>
            <input
              type="text"
              placeholder="e.g., Follow up with prospect"
              value={step.taskTemplate || ''}
              onChange={(e) => onUpdate({ taskTemplate: e.target.value })}
            />
          </div>
        )}

        {step.stepType === 'condition' && (
          <div className="condition-config">
            <label>Condition</label>
            <select
              value={step.condition || ''}
              onChange={(e) => onUpdate({ condition: e.target.value })}
            >
              <option value="">Select condition...</option>
              <option value="email_opened">Previous email opened</option>
              <option value="email_clicked">Previous email clicked</option>
              <option value="email_replied">Prospect replied</option>
            </select>

            <div className="branch-config">
              <div className="branch">
                <label>If true, go to step:</label>
                <input
                  type="number"
                  value={step.conditionTrueStep || ''}
                  onChange={(e) => onUpdate({ conditionTrueStep: parseInt(e.target.value) || undefined })}
                  min={1}
                  max={totalSteps}
                />
              </div>
              <div className="branch">
                <label>If false, go to step:</label>
                <input
                  type="number"
                  value={step.conditionFalseStep || ''}
                  onChange={(e) => onUpdate({ conditionFalseStep: parseInt(e.target.value) || undefined })}
                  min={1}
                  max={totalSteps}
                />
              </div>
            </div>
          </div>
        )}

        {step.stepType !== 'wait' && step.stepType !== 'condition' && (
          <div className="delay-config">
            <label>Delay from previous step:</label>
            <input
              type="number"
              value={step.delayHours || 0}
              onChange={(e) => onUpdate({ delayHours: parseInt(e.target.value) || 0 })}
              min={0}
            />
            <span>hours</span>
          </div>
        )}
      </div>

      <style jsx>{`
        .step-editor {
          padding: 1rem;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .step-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }

        .step-number {
          width: 1.5rem;
          height: 1.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
          color: white;
          background: #3b82f6;
          border-radius: 9999px;
        }

        .step-icon {
          font-size: 1.25rem;
        }

        .step-type {
          font-weight: 500;
          color: #1e293b;
        }

        .step-controls {
          margin-left: auto;
          display: flex;
          gap: 0.25rem;
        }

        .control-btn {
          width: 1.5rem;
          height: 1.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          color: #64748b;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        .control-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .control-btn.remove:hover {
          color: #ef4444;
          border-color: #ef4444;
        }

        .step-content {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .step-content label {
          font-size: 0.75rem;
          color: #64748b;
        }

        .step-content input,
        .step-content select {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          font-size: 0.875rem;
        }

        .wait-config,
        .delay-config {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .wait-config input,
        .delay-config input {
          width: 80px;
        }

        .wait-config span,
        .delay-config span {
          font-size: 0.875rem;
          color: #64748b;
        }

        .condition-config {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .branch-config {
          display: flex;
          gap: 1rem;
          margin-top: 0.5rem;
        }

        .branch {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .branch input {
          width: 60px;
        }
      `}</style>
    </div>
  );
}

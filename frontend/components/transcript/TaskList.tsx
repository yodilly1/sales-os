'use client';

import { useState } from 'react';
import {
  CheckCircle,
  Circle,
  Calendar,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  ArrowRight,
  Phone,
  FileText,
  Users,
  Presentation,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardBody } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { cn, formatDate } from '@/lib/utils';
import { SuggestedTask } from '@/lib/types';

interface TaskListProps {
  tasks: SuggestedTask[];
  onToggleTask: (taskId: string, completed: boolean) => Promise<void>;
  onPushToCRM?: (taskId: string) => Promise<void>;
  className?: string;
}

const priorityConfig = {
  high: { label: 'High', variant: 'danger' as const, icon: AlertTriangle },
  medium: { label: 'Medium', variant: 'warning' as const, icon: null },
  low: { label: 'Low', variant: 'neutral' as const, icon: null },
};

const typeIcons = {
  follow_up: Phone,
  research: FileText,
  internal: Users,
  proposal: FileText,
  demo: Presentation,
};

export function TaskList({
  tasks,
  onToggleTask,
  onPushToCRM,
  className,
}: TaskListProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState<Set<string>>(new Set());

  const completedCount = tasks.filter((t) => t.completed).length;
  const pendingTasks = tasks.filter((t) => !t.completed);
  const completedTasks = tasks.filter((t) => t.completed);

  const handleToggle = async (task: SuggestedTask) => {
    setLoadingTasks((prev) => new Set(prev).add(task.id));
    try {
      await onToggleTask(task.id, !task.completed);
    } finally {
      setLoadingTasks((prev) => {
        const next = new Set(prev);
        next.delete(task.id);
        return next;
      });
    }
  };

  const handlePushToCRM = async (taskId: string) => {
    if (!onPushToCRM) return;
    setLoadingTasks((prev) => new Set(prev).add(`crm-${taskId}`));
    try {
      await onPushToCRM(taskId);
    } finally {
      setLoadingTasks((prev) => {
        const next = new Set(prev);
        next.delete(`crm-${taskId}`);
        return next;
      });
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <CardTitle>Suggested Follow-ups</CardTitle>
          <Badge variant={completedCount === tasks.length ? 'success' : 'neutral'}>
            {completedCount}/{tasks.length}
          </Badge>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-500"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </button>
      </CardHeader>

      {isExpanded && (
        <CardBody className="space-y-4">
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-neutral-500">
              No suggested tasks for this transcript
            </div>
          ) : (
            <>
              {/* Pending Tasks */}
              {pendingTasks.length > 0 && (
                <div className="space-y-2">
                  {pendingTasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      isLoading={loadingTasks.has(task.id)}
                      isCRMLoading={loadingTasks.has(`crm-${task.id}`)}
                      onToggle={() => handleToggle(task)}
                      onPushToCRM={
                        onPushToCRM ? () => handlePushToCRM(task.id) : undefined
                      }
                    />
                  ))}
                </div>
              )}

              {/* Completed Tasks */}
              {completedTasks.length > 0 && (
                <div className="pt-4 border-t border-neutral-100">
                  <p className="text-sm font-medium text-neutral-500 mb-2">
                    Completed ({completedTasks.length})
                  </p>
                  <div className="space-y-2">
                    {completedTasks.map((task) => (
                      <TaskItem
                        key={task.id}
                        task={task}
                        isLoading={loadingTasks.has(task.id)}
                        onToggle={() => handleToggle(task)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </CardBody>
      )}
    </Card>
  );
}

interface TaskItemProps {
  task: SuggestedTask;
  isLoading: boolean;
  isCRMLoading?: boolean;
  onToggle: () => void;
  onPushToCRM?: () => void;
}

function TaskItem({
  task,
  isLoading,
  isCRMLoading,
  onToggle,
  onPushToCRM,
}: TaskItemProps) {
  const TypeIcon = typeIcons[task.type] || FileText;
  const priorityInfo = priorityConfig[task.priority];

  return (
    <div
      className={cn(
        'group flex items-start gap-3 p-3 rounded-lg border transition-colors',
        task.completed
          ? 'bg-neutral-50 border-neutral-100'
          : 'bg-white border-neutral-200 hover:border-neutral-300'
      )}
    >
      {/* Checkbox */}
      <button
        onClick={onToggle}
        disabled={isLoading}
        className={cn(
          'mt-0.5 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded',
          isLoading && 'opacity-50'
        )}
      >
        {task.completed ? (
          <CheckCircle className="w-5 h-5 text-success-500" />
        ) : (
          <Circle className="w-5 h-5 text-neutral-300 hover:text-neutral-400" />
        )}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <TypeIcon className="w-4 h-4 text-neutral-400" />
          <h4
            className={cn(
              'font-medium text-sm',
              task.completed ? 'text-neutral-500 line-through' : 'text-neutral-900'
            )}
          >
            {task.title}
          </h4>
        </div>
        <p
          className={cn(
            'text-sm',
            task.completed ? 'text-neutral-400' : 'text-neutral-600'
          )}
        >
          {task.description}
        </p>

        {/* Meta info */}
        <div className="flex items-center gap-3 mt-2">
          <Badge variant={priorityInfo.variant} size="sm">
            {priorityInfo.label} Priority
          </Badge>

          {task.dueDate && (
            <span className="flex items-center gap-1 text-xs text-neutral-500">
              <Calendar className="w-3 h-3" />
              {formatDate(task.dueDate)}
            </span>
          )}

          {task.crmTaskId && (
            <span className="text-xs text-success-600">Synced to CRM</span>
          )}
        </div>
      </div>

      {/* Actions */}
      {!task.completed && onPushToCRM && !task.crmTaskId && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onPushToCRM}
          isLoading={isCRMLoading}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ArrowRight className="w-4 h-4 mr-1" />
          Push to CRM
        </Button>
      )}
    </div>
  );
}

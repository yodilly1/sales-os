/**
 * Follow-up automation components.
 *
 * This module exports all follow-up related components for use in the Sales OS frontend.
 */

export { FollowUpList } from './FollowUpList';
export { FollowUpCard } from './FollowUpCard';
export { EmailDraftEditor } from './EmailDraftEditor';
export { TaskCard } from './TaskCard';
export { ContentRecommendations } from './ContentRecommendations';
export { MeetingSuggestion } from './MeetingSuggestion';
export { SequenceBuilder } from './SequenceBuilder';
export { SequenceTimeline } from './SequenceTimeline';
export { ApprovalQueue } from './ApprovalQueue';
export { ScheduleCalendar } from './ScheduleCalendar';

// Types
export type {
  FollowUp,
  FollowUpEmail,
  FollowUpTask,
  ContentRecommendation,
  MeetingSuggestionData,
  Sequence,
  SequenceStep,
} from './types';

/**
 * TypeScript types for follow-up components.
 */

export type FollowUpType = 'email' | 'task' | 'content_recommendation' | 'meeting_suggestion';

export type FollowUpStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'scheduled'
  | 'sent'
  | 'completed'
  | 'cancelled'
  | 'failed';

export type Priority = 'low' | 'medium' | 'high' | 'urgent';

export type ApprovalMode = 'auto' | 'manual';

export interface FollowUpBase {
  id: string;
  callId: string;
  prospectId: string;
  type: FollowUpType;
  status: FollowUpStatus;
  priority: Priority;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  spicedAnalysisId?: string;
  scheduledAt?: string;
  sentAt?: string;
  approvalMode: ApprovalMode;
  approvedBy?: string;
  approvedAt?: string;
  sequenceId?: string;
  sequenceStep?: number;
  crmTaskId?: string;
  crmSyncedAt?: string;
}

export interface EmailDraft {
  subject: string;
  bodyHtml: string;
  bodyText: string;
  tokensUsed: string[];
  generationPrompt?: string;
  generationModel?: string;
  confidenceScore?: number;
}

export interface EmailRecipient {
  email: string;
  name: string;
  role?: string;
  company?: string;
}

export interface FollowUpEmail extends FollowUpBase {
  type: 'email';
  recipient: EmailRecipient;
  cc: EmailRecipient[];
  bcc: EmailRecipient[];
  draft: EmailDraft;
  replyToMessageId?: string;
  threadId?: string;
  openedAt?: string;
  clickedAt?: string;
  repliedAt?: string;
}

export type TaskCategory =
  | 'call'
  | 'email'
  | 'meeting'
  | 'research'
  | 'proposal'
  | 'demo'
  | 'internal'
  | 'other';

export interface FollowUpTask extends FollowUpBase {
  type: 'task';
  title: string;
  description?: string;
  category: TaskCategory;
  dueAt?: string;
  reminderAt?: string;
  assignedTo?: string;
  completedAt?: string;
  completionNotes?: string;
}

export type ContentType =
  | 'case_study'
  | 'proposal'
  | 'one_pager'
  | 'battlecard'
  | 'demo_video'
  | 'pricing_sheet'
  | 'whitepaper'
  | 'roi_calculator';

export interface ContentRecommendation {
  contentType: ContentType;
  title: string;
  description: string;
  contentId?: string;
  relevanceScore: number;
  reasoning: string;
  spicedElementsAddressed: string[];
}

export interface FollowUpContentRecommendation extends FollowUpBase {
  type: 'content_recommendation';
  recommendations: ContentRecommendation[];
  primaryRecommendation?: ContentRecommendation;
  selectedContentId?: string;
  selectedAt?: string;
}

export type MeetingType =
  | 'discovery'
  | 'demo'
  | 'technical_deep_dive'
  | 'proposal_review'
  | 'negotiation'
  | 'executive_briefing'
  | 'check_in'
  | 'onboarding';

export interface MeetingSuggestionData {
  meetingType: MeetingType;
  title: string;
  description: string;
  suggestedDurationMinutes: number;
  suggestedAttendees: string[];
  suggestedDates: string[];
  agenda: string[];
  reasoning: string;
  spicedFocusAreas: string[];
}

export interface FollowUpMeetingSuggestion extends FollowUpBase {
  type: 'meeting_suggestion';
  suggestion: MeetingSuggestionData;
  bookingLink?: string;
  bookedAt?: string;
  calendarEventId?: string;
}

export type FollowUp =
  | FollowUpEmail
  | FollowUpTask
  | FollowUpContentRecommendation
  | FollowUpMeetingSuggestion;

export type SequenceStatus = 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';

export type SequenceStepType = 'email' | 'task' | 'wait' | 'condition';

export interface SequenceStep {
  stepNumber: number;
  stepType: SequenceStepType;
  delayHours: number;
  emailTemplateId?: string;
  taskTemplate?: string;
  condition?: string;
  conditionTrueStep?: number;
  conditionFalseStep?: number;
  executedAt?: string;
  status: FollowUpStatus;
}

export interface Sequence {
  id: string;
  name: string;
  description?: string;
  steps: SequenceStep[];
  totalSteps: number;
  status: SequenceStatus;
  currentStep: number;
  prospectId: string;
  callId?: string;
  startedAt?: string;
  completedAt?: string;
  pausedAt?: string;
  approvalMode: ApprovalMode;
  stopOnReply: boolean;
  businessHoursOnly: boolean;
  createdAt: string;
  createdBy?: string;
}

export interface FollowUpGenerationRequest {
  callId: string;
  transcriptId?: string;
  spicedContext: {
    situation?: string;
    pain?: string;
    impact?: string;
    criticalEvent?: string;
    expectedDecision?: string;
    decisionCriteria?: string;
    keyQuotes: string[];
    actionItems: string[];
    objectionsRaised: string[];
  };
  prospectContext: {
    name: string;
    email: string;
    title?: string;
    company: string;
    industry?: string;
    companySize?: string;
    previousCalls: number;
    previousEmailsSent: number;
    lastInteractionDate?: string;
  };
  generateEmail: boolean;
  generateTasks: boolean;
  generateContentRecommendations: boolean;
  generateMeetingSuggestions: boolean;
  approvalMode: ApprovalMode;
  tone: 'professional' | 'casual' | 'formal';
  urgencyLevel: Priority;
  senderName: string;
  senderTitle?: string;
  senderCompany: string;
}

export interface FollowUpGenerationResponse {
  requestId: string;
  callId: string;
  emails: FollowUpEmail[];
  tasks: FollowUpTask[];
  contentRecommendations: FollowUpContentRecommendation[];
  meetingSuggestions: FollowUpMeetingSuggestion[];
  generatedAt: string;
  generationTimeMs?: number;
  modelUsed?: string;
  totalItems: number;
}

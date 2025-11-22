"""
Follow-up automation data models.

Defines Pydantic models for follow-up emails, tasks, content recommendations,
meeting suggestions, sequences, and scheduling.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr


class FollowUpType(str, Enum):
    """Types of follow-up actions."""
    EMAIL = "email"
    TASK = "task"
    CONTENT_RECOMMENDATION = "content_recommendation"
    MEETING_SUGGESTION = "meeting_suggestion"


class FollowUpStatus(str, Enum):
    """Status of a follow-up item."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    SENT = "sent"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ApprovalMode(str, Enum):
    """Approval workflow mode."""
    AUTO = "auto"  # Automatically approve and send
    MANUAL = "manual"  # Requires manual approval before sending


class Priority(str, Enum):
    """Priority levels for follow-ups."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ContentType(str, Enum):
    """Types of content that can be recommended."""
    CASE_STUDY = "case_study"
    PROPOSAL = "proposal"
    ONE_PAGER = "one_pager"
    BATTLECARD = "battlecard"
    DEMO_VIDEO = "demo_video"
    PRICING_SHEET = "pricing_sheet"
    WHITEPAPER = "whitepaper"
    ROI_CALCULATOR = "roi_calculator"


# ============================================================================
# Base Models
# ============================================================================


class FollowUpBase(BaseModel):
    """Base model for all follow-up types."""
    id: UUID = Field(default_factory=uuid4)
    call_id: UUID
    prospect_id: UUID
    type: FollowUpType
    status: FollowUpStatus = FollowUpStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

    # SPICED context that generated this follow-up
    spiced_analysis_id: Optional[UUID] = None

    # Scheduling
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    # Approval workflow
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    # Sequence tracking
    sequence_id: Optional[UUID] = None
    sequence_step: Optional[int] = None

    # CRM sync
    crm_task_id: Optional[str] = None
    crm_synced_at: Optional[datetime] = None


# ============================================================================
# Email Follow-Up Models
# ============================================================================


class EmailDraft(BaseModel):
    """Email draft content."""
    subject: str = Field(..., min_length=1, max_length=200)
    body_html: str
    body_text: str

    # Personalization tokens used
    tokens_used: list[str] = Field(default_factory=list)

    # AI generation metadata
    generation_prompt: Optional[str] = None
    generation_model: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class EmailRecipient(BaseModel):
    """Email recipient information."""
    email: EmailStr
    name: str
    role: Optional[str] = None
    company: Optional[str] = None


class FollowUpEmail(FollowUpBase):
    """Follow-up email model."""
    type: FollowUpType = FollowUpType.EMAIL

    # Recipient info
    recipient: EmailRecipient
    cc: list[EmailRecipient] = Field(default_factory=list)
    bcc: list[EmailRecipient] = Field(default_factory=list)

    # Email content
    draft: EmailDraft

    # Reply tracking
    reply_to_message_id: Optional[str] = None
    thread_id: Optional[str] = None

    # Engagement tracking
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None


# ============================================================================
# Task/Reminder Models
# ============================================================================


class TaskCategory(str, Enum):
    """Categories of tasks."""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    RESEARCH = "research"
    PROPOSAL = "proposal"
    DEMO = "demo"
    INTERNAL = "internal"
    OTHER = "other"


class FollowUpTask(FollowUpBase):
    """Follow-up task/reminder model."""
    type: FollowUpType = FollowUpType.TASK

    # Task details
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.OTHER

    # Due date
    due_at: Optional[datetime] = None
    reminder_at: Optional[datetime] = None

    # Assignment
    assigned_to: Optional[UUID] = None

    # Completion
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None


# ============================================================================
# Content Recommendation Models
# ============================================================================


class ContentRecommendation(BaseModel):
    """Recommended content to send."""
    content_type: ContentType
    title: str
    description: str
    content_id: Optional[UUID] = None  # Reference to existing content
    relevance_score: float = Field(..., ge=0.0, le=1.0)

    # Why this content is recommended
    reasoning: str

    # SPICED alignment
    spiced_elements_addressed: list[str] = Field(default_factory=list)


class FollowUpContentRecommendation(FollowUpBase):
    """Follow-up content recommendation model."""
    type: FollowUpType = FollowUpType.CONTENT_RECOMMENDATION

    # Recommended content items
    recommendations: list[ContentRecommendation] = Field(default_factory=list)

    # Top recommendation
    primary_recommendation: Optional[ContentRecommendation] = None

    # Selected content (after user picks)
    selected_content_id: Optional[UUID] = None
    selected_at: Optional[datetime] = None


# ============================================================================
# Meeting Suggestion Models
# ============================================================================


class MeetingType(str, Enum):
    """Types of meetings."""
    DISCOVERY = "discovery"
    DEMO = "demo"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    PROPOSAL_REVIEW = "proposal_review"
    NEGOTIATION = "negotiation"
    EXECUTIVE_BRIEFING = "executive_briefing"
    CHECK_IN = "check_in"
    ONBOARDING = "onboarding"


class MeetingSuggestion(BaseModel):
    """Suggested meeting details."""
    meeting_type: MeetingType
    title: str
    description: str
    suggested_duration_minutes: int = 30
    suggested_attendees: list[str] = Field(default_factory=list)

    # Suggested time windows
    suggested_dates: list[datetime] = Field(default_factory=list)

    # Agenda items
    agenda: list[str] = Field(default_factory=list)

    # Why this meeting is suggested
    reasoning: str

    # SPICED elements to address in meeting
    spiced_focus_areas: list[str] = Field(default_factory=list)


class FollowUpMeetingSuggestion(FollowUpBase):
    """Follow-up meeting suggestion model."""
    type: FollowUpType = FollowUpType.MEETING_SUGGESTION

    # Meeting suggestion
    suggestion: MeetingSuggestion

    # Booking status
    booking_link: Optional[str] = None
    booked_at: Optional[datetime] = None
    calendar_event_id: Optional[str] = None


# ============================================================================
# Sequence Models (Multi-touch Campaigns)
# ============================================================================


class SequenceStatus(str, Enum):
    """Status of a sequence."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SequenceStepType(str, Enum):
    """Types of steps in a sequence."""
    EMAIL = "email"
    TASK = "task"
    WAIT = "wait"
    CONDITION = "condition"


class SequenceStep(BaseModel):
    """A step in a follow-up sequence."""
    step_number: int
    step_type: SequenceStepType

    # Delay before this step (in hours)
    delay_hours: int = 0

    # Step content (based on type)
    email_template_id: Optional[UUID] = None
    task_template: Optional[str] = None

    # Condition for branching
    condition: Optional[str] = None
    condition_true_step: Optional[int] = None
    condition_false_step: Optional[int] = None

    # Execution tracking
    executed_at: Optional[datetime] = None
    status: FollowUpStatus = FollowUpStatus.DRAFT


class FollowUpSequence(BaseModel):
    """Multi-touch follow-up sequence."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None

    # Sequence configuration
    steps: list[SequenceStep] = Field(default_factory=list)
    total_steps: int = 0

    # Status tracking
    status: SequenceStatus = SequenceStatus.DRAFT
    current_step: int = 0

    # Target
    prospect_id: UUID
    call_id: Optional[UUID] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None

    # Settings
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    stop_on_reply: bool = True
    business_hours_only: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None


# ============================================================================
# Schedule Models
# ============================================================================


class ScheduleWindow(BaseModel):
    """Time window for scheduling."""
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=0, le=23)
    days_of_week: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    timezone: str = "UTC"


class ScheduleConfig(BaseModel):
    """Configuration for follow-up scheduling."""
    id: UUID = Field(default_factory=uuid4)
    name: str

    # Default schedule window
    window: ScheduleWindow

    # Optimal send times (learned from engagement)
    optimal_send_times: list[int] = Field(default_factory=list)  # Hours in UTC

    # Blackout dates (holidays, etc.)
    blackout_dates: list[datetime] = Field(default_factory=list)

    # Limits
    max_emails_per_day: int = 50
    max_emails_per_prospect_per_day: int = 2
    min_hours_between_emails: int = 4


# ============================================================================
# CRM Sync Models
# ============================================================================


class CRMTaskStatus(str, Enum):
    """Status of CRM task sync."""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    SKIPPED = "skipped"


class CRMSyncRecord(BaseModel):
    """Record of CRM sync operation."""
    id: UUID = Field(default_factory=uuid4)
    followup_id: UUID
    followup_type: FollowUpType

    # CRM details
    crm_type: str = "hubspot"  # hubspot, salesforce, etc.
    crm_object_type: str  # task, note, activity, etc.
    crm_object_id: Optional[str] = None

    # Sync status
    status: CRMTaskStatus = CRMTaskStatus.PENDING
    synced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    # Payload
    request_payload: Optional[dict] = None
    response_payload: Optional[dict] = None


# ============================================================================
# Generation Request/Response Models
# ============================================================================


class SPICEDContext(BaseModel):
    """SPICED analysis context for generation."""
    situation: Optional[str] = None
    pain: Optional[str] = None
    impact: Optional[str] = None
    critical_event: Optional[str] = None
    expected_decision: Optional[str] = None
    decision_criteria: Optional[str] = None

    # Additional context
    key_quotes: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    objections_raised: list[str] = Field(default_factory=list)


class ProspectContext(BaseModel):
    """Prospect context for personalization."""
    name: str
    email: EmailStr
    title: Optional[str] = None
    company: str
    industry: Optional[str] = None
    company_size: Optional[str] = None

    # Engagement history
    previous_calls: int = 0
    previous_emails_sent: int = 0
    last_interaction_date: Optional[datetime] = None


class FollowUpGenerationRequest(BaseModel):
    """Request to generate follow-ups from a call."""
    call_id: UUID
    transcript_id: Optional[UUID] = None

    # Context
    spiced_context: SPICEDContext
    prospect_context: ProspectContext

    # Generation options
    generate_email: bool = True
    generate_tasks: bool = True
    generate_content_recommendations: bool = True
    generate_meeting_suggestions: bool = True

    # Preferences
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    tone: str = "professional"  # professional, casual, formal
    urgency_level: Priority = Priority.MEDIUM

    # Sender info
    sender_name: str
    sender_title: Optional[str] = None
    sender_company: str


class FollowUpGenerationResponse(BaseModel):
    """Response containing generated follow-ups."""
    request_id: UUID = Field(default_factory=uuid4)
    call_id: UUID

    # Generated follow-ups
    emails: list[FollowUpEmail] = Field(default_factory=list)
    tasks: list[FollowUpTask] = Field(default_factory=list)
    content_recommendations: list[FollowUpContentRecommendation] = Field(default_factory=list)
    meeting_suggestions: list[FollowUpMeetingSuggestion] = Field(default_factory=list)

    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_ms: Optional[int] = None
    model_used: Optional[str] = None

    # Summary
    total_items: int = 0

    def model_post_init(self, __context) -> None:
        """Calculate total items after initialization."""
        self.total_items = (
            len(self.emails) +
            len(self.tasks) +
            len(self.content_recommendations) +
            len(self.meeting_suggestions)
        )


# ============================================================================
# API Request/Response Models
# ============================================================================


class FollowUpListRequest(BaseModel):
    """Request to list follow-ups."""
    prospect_id: Optional[UUID] = None
    call_id: Optional[UUID] = None
    status: Optional[FollowUpStatus] = None
    type: Optional[FollowUpType] = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    # Sorting
    sort_by: str = "created_at"
    sort_order: str = "desc"


class FollowUpApprovalRequest(BaseModel):
    """Request to approve a follow-up."""
    followup_id: UUID
    approved: bool

    # Optional modifications before approval
    modifications: Optional[dict] = None

    # Scheduling (if approved)
    schedule_at: Optional[datetime] = None

    # Notes
    approval_notes: Optional[str] = None


class FollowUpScheduleRequest(BaseModel):
    """Request to schedule a follow-up."""
    followup_id: UUID
    scheduled_at: datetime

    # Override default schedule config
    ignore_schedule_window: bool = False
    ignore_blackout_dates: bool = False


class FollowUpBulkActionRequest(BaseModel):
    """Request for bulk actions on follow-ups."""
    followup_ids: list[UUID]
    action: str  # approve, cancel, reschedule, send

    # Action-specific parameters
    schedule_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

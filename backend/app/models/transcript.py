<<<<<<< HEAD
"""Transcript and call note data models.

Supports various transcript formats from different meeting platforms:
- Zoom
- Microsoft Teams
- Avoma
- Generic/Other
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .spiced import SPICEDAnalysis


class TranscriptFormat(str, Enum):
    """Supported transcript source formats."""

    ZOOM = "zoom"
    TEAMS = "teams"
    AVOMA = "avoma"
    GONG = "gong"
    CHORUS = "chorus"
    GENERIC = "generic"


class TranscriptSpeaker(BaseModel):
    """A speaker in the transcript."""

    id: Optional[str] = Field(default=None, description="Unique speaker identifier")
    name: str = Field(..., description="Speaker name")
    role: Optional[str] = Field(
        default=None,
        description="Speaker role (e.g., 'sales_rep', 'prospect', 'unknown')",
    )
    email: Optional[str] = Field(default=None, description="Speaker email if available")
    company: Optional[str] = Field(
        default=None, description="Speaker's company if identified"
    )


class TranscriptTurn(BaseModel):
    """A single turn/utterance in the transcript."""

    speaker: str = Field(..., description="Name of the speaker")
    text: str = Field(..., description="What was said")
    timestamp: Optional[str] = Field(
        default=None, description="Timestamp in the recording"
    )
    start_time: Optional[float] = Field(
        default=None, description="Start time in seconds"
    )
    end_time: Optional[float] = Field(default=None, description="End time in seconds")


class Transcript(BaseModel):
    """A parsed transcript from a sales call."""

    id: Optional[str] = Field(default=None, description="Unique transcript identifier")
    title: Optional[str] = Field(default=None, description="Call/meeting title")
    format: TranscriptFormat = Field(
        default=TranscriptFormat.GENERIC,
        description="Source format of the transcript",
    )
    raw_text: str = Field(..., description="The original raw transcript text")
    turns: list[TranscriptTurn] = Field(
        default_factory=list,
        description="Parsed conversation turns",
    )
    speakers: list[TranscriptSpeaker] = Field(
        default_factory=list,
        description="Identified speakers in the call",
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Call duration in minutes",
    )
    call_date: Optional[datetime] = Field(
        default=None,
        description="Date and time of the call",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata from the source platform",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this transcript was processed",
    )


class TaskPriority(str, Enum):
    """Priority levels for follow-up tasks."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FollowUpTask(BaseModel):
    """A recommended follow-up task generated from the transcript."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority",
    )
    due_date_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested due date or timeframe",
    )
    assignee_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested assignee (role or name)",
    )
    related_spiced_component: Optional[str] = Field(
        default=None,
        description="Which SPICED component this task relates to",
    )
    crm_task_type: Optional[str] = Field(
        default=None,
        description="Suggested CRM task type (call, email, meeting, etc.)",
    )


class CallNote(BaseModel):
    """Formatted call notes generated from the transcript analysis."""

    summary: str = Field(
        ...,
        description="Executive summary of the call",
    )
    attendees: list[str] = Field(
        default_factory=list,
        description="List of call attendees",
    )
    key_discussion_points: list[str] = Field(
        default_factory=list,
        description="Main topics discussed",
    )
    customer_sentiment: Optional[str] = Field(
        default=None,
        description="Overall customer sentiment assessment",
    )
    next_steps_discussed: list[str] = Field(
        default_factory=list,
        description="Next steps mentioned during the call",
    )
    objections_raised: list[str] = Field(
        default_factory=list,
        description="Any objections or concerns raised",
    )
    questions_asked: list[str] = Field(
        default_factory=list,
        description="Key questions asked by the prospect",
    )
    commitments_made: list[str] = Field(
        default_factory=list,
        description="Commitments made by either party",
    )
    formatted_note: str = Field(
        ...,
        description="Full formatted call note for CRM",
    )


class TranscriptParseRequest(BaseModel):
    """Request to parse a transcript and extract SPICED information."""

    transcript_text: str = Field(
        ...,
        min_length=50,
        description="The raw transcript text to parse",
    )
    format: TranscriptFormat = Field(
        default=TranscriptFormat.GENERIC,
        description="Source format hint for better parsing",
    )
    call_title: Optional[str] = Field(
        default=None,
        description="Title of the call/meeting",
    )
    call_date: Optional[datetime] = Field(
        default=None,
        description="Date of the call",
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Prospect company name if known",
    )
    sales_rep_name: Optional[str] = Field(
        default=None,
        description="Name of the sales rep for speaker identification",
    )
    generate_tasks: bool = Field(
        default=True,
        description="Whether to generate follow-up task recommendations",
    )
    generate_call_note: bool = Field(
        default=True,
        description="Whether to generate formatted call notes",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "transcript_text": """
John (Sales Rep): Hi Sarah, thanks for taking the time to meet today.

Sarah (Prospect): Of course, we've been looking at solutions like yours for a while now.

John: Great to hear. Can you tell me a bit about what's driving your search?

Sarah: Well, our sales team is growing rapidly - we just hit 50 reps - and our current
tools aren't keeping up. We're using Salesforce but the data quality is terrible because
reps hate updating it.

John: That's a common challenge. How is that impacting your business?

Sarah: It's brutal. We estimate we're losing about 20% of selling time to administrative
work. Our VP thinks that's costing us around $2M in pipeline we should be building.

John: That's significant. Is there a timeline you're working against?

Sarah: Yes, we need to have something in place before Q4 planning, so really by end of
October at the latest. Our VP of Sales, Mike, will make the final call but he needs
CFO sign-off on budget.
""",
                "format": "generic",
                "call_title": "Discovery Call - Acme Corp",
                "company_name": "Acme Corp",
                "sales_rep_name": "John",
            }
        }


class TranscriptParseResponse(BaseModel):
    """Response from transcript parsing with SPICED analysis."""

    transcript: Transcript = Field(
        ...,
        description="The parsed transcript",
    )
    spiced_analysis: SPICEDAnalysis = Field(
        ...,
        description="Extracted SPICED analysis",
    )
    call_note: Optional[CallNote] = Field(
        default=None,
        description="Formatted call notes",
    )
    follow_up_tasks: list[FollowUpTask] = Field(
        default_factory=list,
        description="Recommended follow-up tasks",
    )
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Time taken to process the transcript",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings or notes about the analysis",
    )
=======
"""Transcript and SPICED analysis models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseDBModel, BaseModel, TimestampedSchema


class TranscriptSource(str, Enum):
    """Source of the transcript."""

    AVOMA = "avoma"
    ZOOM = "zoom"
    TEAMS = "teams"
    GONG = "gong"
    MANUAL = "manual"


class Transcript(BaseDBModel):
    """Call transcript model."""

    __tablename__ = "transcripts"

    title = Column(String(500), nullable=False)
    source = Column(SQLEnum(TranscriptSource), default=TranscriptSource.MANUAL)
    source_id = Column(String(255))  # External ID from source system
    raw_text = Column(Text, nullable=False)
    duration_seconds = Column(Integer)
    call_date = Column(String(50))  # ISO date string
    participants = Column(JSON, default=list)  # List of participant names/emails
    metadata = Column(JSON, default=dict)

    # Relationships
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    prospect_id = Column(String(36), ForeignKey("prospects.id"))


class SPICEDAnalysis(BaseDBModel):
    """SPICED analysis extracted from transcript."""

    __tablename__ = "spiced_analyses"

    transcript_id = Column(
        String(36), ForeignKey("transcripts.id"), nullable=False, unique=True
    )

    # SPICED Fields
    situation = Column(Text)  # Current state/context
    situation_confidence = Column(Integer, default=0)  # 0-100

    pain = Column(Text)  # Problems/challenges identified
    pain_confidence = Column(Integer, default=0)

    impact = Column(Text)  # Business consequences
    impact_confidence = Column(Integer, default=0)

    critical_event = Column(Text)  # Timeline/urgency drivers
    critical_event_confidence = Column(Integer, default=0)

    expected_decision = Column(Text)  # Decision process
    expected_decision_confidence = Column(Integer, default=0)

    decision_criteria = Column(Text)  # Evaluation criteria
    decision_criteria_confidence = Column(Integer, default=0)

    # Summary and suggestions
    summary = Column(Text)
    key_quotes = Column(JSON, default=list)  # List of notable quotes
    follow_up_tasks = Column(JSON, default=list)  # Suggested next steps
    objections = Column(JSON, default=list)  # Objections raised

    # Analysis metadata
    model_version = Column(String(50))
    analysis_date = Column(String(50))


# Pydantic Schemas
class SPICEDField(BaseModel):
    """Single SPICED field with confidence."""

    content: Optional[str] = None
    confidence: int = 0


class SPICEDAnalysisSchema(TimestampedSchema):
    """SPICED analysis response schema."""

    transcript_id: str
    situation: SPICEDField
    pain: SPICEDField
    impact: SPICEDField
    critical_event: SPICEDField
    expected_decision: SPICEDField
    decision_criteria: SPICEDField
    summary: Optional[str] = None
    key_quotes: List[str] = []
    follow_up_tasks: List[str] = []
    objections: List[str] = []


class TranscriptSchema(TimestampedSchema):
    """Transcript response schema."""

    title: str
    source: TranscriptSource
    source_id: Optional[str] = None
    raw_text: str
    duration_seconds: Optional[int] = None
    call_date: Optional[str] = None
    participants: List[str] = []
    metadata: Dict[str, Any] = {}
    user_id: str
    organization_id: str
    prospect_id: Optional[str] = None
    spiced_analysis: Optional[SPICEDAnalysisSchema] = None


class TranscriptCreate(BaseModel):
    """Transcript creation schema."""

    title: str
    source: TranscriptSource = TranscriptSource.MANUAL
    source_id: Optional[str] = None
    raw_text: str
    duration_seconds: Optional[int] = None
    call_date: Optional[str] = None
    participants: List[str] = []
    metadata: Dict[str, Any] = {}
    prospect_id: Optional[str] = None


class TranscriptExport(BaseModel):
    """Transcript export data format."""

    id: str
    title: str
    source: str
    call_date: Optional[str]
    duration_seconds: Optional[int]
    participants: List[str]
    raw_text: str
    spiced: Optional[Dict[str, Any]] = None
    created_at: str
>>>>>>> origin/claude/export-import-service-01K8LsZNbidmjJoTxFQ47hx3

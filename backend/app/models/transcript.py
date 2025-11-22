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

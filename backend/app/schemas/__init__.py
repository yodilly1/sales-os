"""Pydantic schemas for API validation."""
from app.schemas.user import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    TeamBase,
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.transcript import (
    CallBase,
    CallCreate,
    CallResponse,
    CallUpdate,
    TranscriptBase,
    TranscriptCreate,
    TranscriptResponse,
)
from app.schemas.spiced import (
    SPICEDAnalysisBase,
    SPICEDAnalysisCreate,
    SPICEDAnalysisResponse,
    SPICEDScores,
)
from app.schemas.content import (
    ContentBase,
    ContentCreate,
    ContentResponse,
    ContentTemplateBase,
    ContentTemplateCreate,
    ContentTemplateResponse,
    ContentUpdate,
)
from app.schemas.prospect import (
    CompanyBase,
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    ProspectBase,
    ProspectCreate,
    ProspectResponse,
    ProspectUpdate,
)
from app.schemas.coaching import (
    CoachingReportBase,
    CoachingReportCreate,
    CoachingReportResponse,
    CoachingScoreBase,
    CoachingScoreCreate,
    CoachingScoreResponse,
)

__all__ = [
    # User & Organization
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # Transcript & Call
    "CallBase",
    "CallCreate",
    "CallUpdate",
    "CallResponse",
    "TranscriptBase",
    "TranscriptCreate",
    "TranscriptResponse",
    # SPICED
    "SPICEDAnalysisBase",
    "SPICEDAnalysisCreate",
    "SPICEDAnalysisResponse",
    "SPICEDScores",
    # Content
    "ContentBase",
    "ContentCreate",
    "ContentUpdate",
    "ContentResponse",
    "ContentTemplateBase",
    "ContentTemplateCreate",
    "ContentTemplateResponse",
    # Prospect & Company
    "ProspectBase",
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectResponse",
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    # Coaching
    "CoachingScoreBase",
    "CoachingScoreCreate",
    "CoachingScoreResponse",
    "CoachingReportBase",
    "CoachingReportCreate",
    "CoachingReportResponse",
]

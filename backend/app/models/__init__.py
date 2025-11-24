"""Database models for Sales OS."""
from app.models.user import Organization, Team, User
from app.models.transcript import Call, Transcript, SPICEDAnalysis
from app.models.content import Content, ContentTemplate
from app.models.prospect import Company, Prospect
from app.models.coaching import CoachingReport, CoachingScore
from app.models.hubspot import HubSpotIntegration

__all__ = [
    # User & Organization
    "User",
    "Team",
    "Organization",
    # Transcript & Calls
    "Call",
    "Transcript",
    # SPICED Analysis
    "SPICEDAnalysis",
    # Content
    "Content",
    "ContentTemplate",
    # Prospect & Company
    "Prospect",
    "Company",
    # Coaching
    "CoachingReport",
    "CoachingScore",
    # Integrations
    "HubSpotIntegration",
]

"""Application constants."""

from enum import Enum


class ContentType(str, Enum):
    """Supported content types for generation."""

    # Sales Decks
    DECK_PITCH = "deck_pitch"
    DECK_RENEWAL = "deck_renewal"
    DECK_QBR = "deck_qbr"

    # Proposals
    PROPOSAL_CUSTOM = "proposal_custom"
    PROPOSAL_TEMPLATED = "proposal_templated"

    # One-Pagers
    ONE_PAGER_PRODUCT = "one_pager_product"
    ONE_PAGER_SOLUTION = "one_pager_solution"
    ONE_PAGER_CASE_STUDY = "one_pager_case_study"

    # Battlecards
    BATTLECARD_COMPETITIVE = "battlecard_competitive"
    BATTLECARD_OBJECTION = "battlecard_objection"


class ContentStatus(str, Enum):
    """Content generation status."""

    DRAFT = "draft"
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class BrandVoice(str, Enum):
    """Brand voice options for content generation."""

    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class AudienceType(str, Enum):
    """Target audience types."""

    C_SUITE = "c_suite"
    VP_DIRECTOR = "vp_director"
    MANAGER = "manager"
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    TECHNICAL = "technical"
    BUSINESS = "business"


class TokenType(str, Enum):
    """JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"


class OAuthProvider(str, Enum):
    """OAuth provider types."""

    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    HUBSPOT = "hubspot"
    AVOMA = "avoma"


class AuditAction(str, Enum):
    """Audit log action types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    EXPORT = "export"
    IMPORT = "import"


class UserRole(str, Enum):
    """User role types."""

    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


# API Key Header Name
API_KEY_HEADER = "X-API-Key"


# Content type categories for grouping
CONTENT_CATEGORIES = {
    "decks": [ContentType.DECK_PITCH, ContentType.DECK_RENEWAL, ContentType.DECK_QBR],
    "proposals": [ContentType.PROPOSAL_CUSTOM, ContentType.PROPOSAL_TEMPLATED],
    "one_pagers": [
        ContentType.ONE_PAGER_PRODUCT,
        ContentType.ONE_PAGER_SOLUTION,
        ContentType.ONE_PAGER_CASE_STUDY,
    ],
    "battlecards": [ContentType.BATTLECARD_COMPETITIVE, ContentType.BATTLECARD_OBJECTION],
}

# Default slide counts for deck types
DECK_SLIDE_COUNTS = {
    ContentType.DECK_PITCH: 10,
    ContentType.DECK_RENEWAL: 8,
    ContentType.DECK_QBR: 12,
}

# SPICED Framework elements (for WbD alignment)
SPICED_ELEMENTS = [
    "situation",
    "pain",
    "impact",
    "critical_event",
    "expected_decision",
    "decision_criteria",
]

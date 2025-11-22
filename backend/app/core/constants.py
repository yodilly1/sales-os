"""Application constants."""

from enum import Enum


<<<<<<< HEAD
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
=======
class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    MANAGER = "manager"
    REP = "rep"
    VIEWER = "viewer"


class TokenType(str, Enum):
    """Token types for JWT."""

    ACCESS = "access"
    REFRESH = "refresh"


class AuditAction(str, Enum):
    """Audit log action types."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    OAUTH_CONNECTED = "oauth_connected"
    OAUTH_DISCONNECTED = "oauth_disconnected"
    TRANSCRIPT_UPLOADED = "transcript_uploaded"
    CONTENT_GENERATED = "content_generated"
    PROSPECT_ENRICHED = "prospect_enriched"
    COACHING_GENERATED = "coaching_generated"


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    HUBSPOT = "hubspot"
    AVOMA = "avoma"


# API Key settings
API_KEY_HEADER = "X-API-Key"
API_KEY_QUERY_PARAM = "api_key"

# JWT settings
JWT_BEARER_SCHEME = "Bearer"

# Rate limiting
DEFAULT_RATE_LIMIT = "100/minute"
AUTH_RATE_LIMIT = "10/minute"
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef

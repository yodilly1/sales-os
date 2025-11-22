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

"""
Gong Integration Package

Provides integration with Gong conversation intelligence platform
for importing calls, transcripts, and meeting metadata.
"""

from .client import GongClient
from .models import (
    GongAuthConfig,
    GongCall,
    GongTranscript,
    GongParticipant,
    GongCallListResponse,
    GongSyncRequest,
    GongSyncResponse,
)

__all__ = [
    "GongClient",
    "GongAuthConfig",
    "GongCall",
    "GongTranscript",
    "GongParticipant",
    "GongCallListResponse",
    "GongSyncRequest",
    "GongSyncResponse",
]

"""
Gong Integration Utilities

Helper functions for data mapping and processing.
"""

import hashlib
from datetime import datetime
from typing import Optional

from .models import GongCall, GongTranscript, GongParticipant


def generate_call_hash(call_id: str, workspace_id: Optional[str] = None) -> str:
    """
    Generate a unique hash for a Gong call for deduplication.

    Args:
        call_id: Gong call ID
        workspace_id: Optional workspace ID

    Returns:
        SHA256 hash string
    """
    data = f"gong:{call_id}"
    if workspace_id:
        data += f":{workspace_id}"
    return hashlib.sha256(data.encode()).hexdigest()


def map_gong_call_to_internal(call: GongCall) -> dict:
    """
    Map a Gong call to internal data model format.

    Args:
        call: GongCall object

    Returns:
        Dictionary matching internal call/meeting schema
    """
    return {
        "source": "gong",
        "external_id": call.id,
        "external_hash": generate_call_hash(call.id, call.workspace_id),
        "title": call.title,
        "scheduled_at": call.scheduled.isoformat() if call.scheduled else None,
        "started_at": call.started.isoformat() if call.started else None,
        "duration_seconds": call.duration,
        "direction": call.direction,
        "platform": call.system,  # e.g., "Zoom", "Teams"
        "scope": call.scope,  # "Internal", "External"
        "media_type": call.media,  # "Video", "Audio"
        "language": call.language,
        "external_url": call.url,
        "metadata": {
            "workspace_id": call.workspace_id,
            "sdr_disposition": call.sdr_disposition,
            "client_unique_id": call.client_unique_id,
            "custom_data": call.custom_data,
        },
    }


def map_gong_transcript_to_internal(transcript: GongTranscript) -> dict:
    """
    Map a Gong transcript to internal format.

    Args:
        transcript: GongTranscript object

    Returns:
        Dictionary matching internal transcript schema
    """
    return {
        "source": "gong",
        "external_call_id": transcript.call_id,
        "raw_text": transcript.to_text(),
        "formatted_text": transcript.to_formatted_text(),
        "segments": transcript.segments,
        "segment_count": len(transcript.segments),
    }


def map_gong_participant_to_internal(participant: GongParticipant) -> dict:
    """
    Map a Gong participant to internal contact format.

    Args:
        participant: GongParticipant object

    Returns:
        Dictionary matching internal contact schema
    """
    return {
        "source": "gong",
        "external_id": participant.id,
        "email": participant.email,
        "name": participant.name,
        "title": participant.title,
        "phone": participant.phone,
        "is_internal": participant.affiliation == "internal",
        "metadata": {
            "speaker_id": participant.speaker_id,
            "user_id": participant.user_id,
            "context": participant.context,
        },
    }


def calculate_talk_time_percentage(
    transcript: GongTranscript, speaker_id: str
) -> Optional[float]:
    """
    Calculate the percentage of talk time for a specific speaker.

    Args:
        transcript: GongTranscript object
        speaker_id: Speaker ID to calculate for

    Returns:
        Percentage of total talk time (0-100) or None
    """
    if not transcript.segments:
        return None

    total_time = 0.0
    speaker_time = 0.0

    for segment in transcript.segments:
        start = segment.get("start_time", 0) or 0
        end = segment.get("end_time", 0) or 0
        duration = end - start

        if duration > 0:
            total_time += duration
            if segment.get("speaker_id") == speaker_id:
                speaker_time += duration

    if total_time == 0:
        return None

    return round((speaker_time / total_time) * 100, 2)


def extract_key_moments(transcript: GongTranscript, keywords: list[str]) -> list[dict]:
    """
    Extract segments containing specific keywords.

    Args:
        transcript: GongTranscript object
        keywords: List of keywords to search for

    Returns:
        List of segments containing keywords
    """
    key_moments = []
    keywords_lower = [kw.lower() for kw in keywords]

    for segment in transcript.segments:
        text = segment.get("text", "").lower()
        for keyword in keywords_lower:
            if keyword in text:
                key_moments.append({
                    "segment": segment,
                    "keyword": keyword,
                    "timestamp": segment.get("start_time"),
                })
                break  # Only add segment once even if multiple keywords match

    return key_moments


def format_duration(seconds: Optional[int]) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds is None:
        return "Unknown"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def is_duplicate_call(call_hash: str, existing_hashes: set[str]) -> bool:
    """
    Check if a call has already been synced.

    Args:
        call_hash: Hash of the call to check
        existing_hashes: Set of already synced call hashes

    Returns:
        True if call is a duplicate
    """
    return call_hash in existing_hashes

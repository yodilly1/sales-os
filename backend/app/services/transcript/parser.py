"""Transcript parser for various meeting platform formats.

Supports parsing transcripts from:
- Zoom
- Microsoft Teams
- Avoma
- Gong
- Chorus
- Generic/plain text formats
"""
import re
import uuid
from datetime import datetime
from typing import Optional

from app.models.transcript import (
    TranscriptData,
    TranscriptFormat,
    TranscriptSpeaker,
    TranscriptTurn,
)


class TranscriptParser:
    """Parser for converting raw transcript text into structured format.

    Supports multiple transcript formats from various meeting platforms.
    """

    # Common patterns for speaker identification
    SPEAKER_PATTERNS = {
        # "Speaker Name: text" or "Speaker Name (role): text"
        "colon": re.compile(
            r"^(?P<speaker>[A-Za-z][A-Za-z\s\.,'()-]*?)(?:\s*\([^)]+\))?\s*:\s*(?P<text>.+)$",
            re.MULTILINE,
        ),
        # "[00:00:00] Speaker Name: text" (timestamped)
        "timestamped": re.compile(
            r"^\[?(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\]?\s*"
            r"(?P<speaker>[A-Za-z][A-Za-z\s\.,'()-]*?)(?:\s*\([^)]+\))?\s*:\s*(?P<text>.+)$",
            re.MULTILINE,
        ),
        # Zoom format: "00:00:00 Speaker Name: text"
        "zoom": re.compile(
            r"^(?P<timestamp>\d{2}:\d{2}:\d{2})\s+"
            r"(?P<speaker>[A-Za-z][A-Za-z\s\.,'()-]+?):\s*(?P<text>.+)$",
            re.MULTILINE,
        ),
        # Teams/VTT format
        "vtt": re.compile(
            r"^(?P<timestamp>\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\s*\n"
            r"<v\s+(?P<speaker>[^>]+)>(?P<text>.+)$",
            re.MULTILINE,
        ),
        # Avoma format: "Speaker Name (Company)\nTimestamp\nText"
        "avoma": re.compile(
            r"^(?P<speaker>[A-Za-z][A-Za-z\s\.,'()-]+?)(?:\s*\([^)]+\))?\s*\n"
            r"(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\s*\n"
            r"(?P<text>.+?)(?=\n\n|\Z)",
            re.MULTILINE | re.DOTALL,
        ),
    }

    # Patterns for identifying roles
    SALES_REP_INDICATORS = [
        "sales",
        "rep",
        "account executive",
        "ae",
        "sdr",
        "bdr",
        "account manager",
        "solutions engineer",
        "se",
    ]

    PROSPECT_INDICATORS = [
        "prospect",
        "customer",
        "client",
        "buyer",
        "vp",
        "director",
        "manager",
        "ceo",
        "cto",
        "cfo",
    ]

    def __init__(self, sales_rep_name: Optional[str] = None):
        """Initialize the parser.

        Args:
            sales_rep_name: Name of the sales rep for role identification
        """
        self.sales_rep_name = sales_rep_name

    def parse(
        self,
        raw_text: str,
        format_hint: TranscriptFormat = TranscriptFormat.GENERIC,
        title: Optional[str] = None,
        call_date: Optional[datetime] = None,
    ) -> TranscriptData:
        """Parse raw transcript text into a structured TranscriptData.

        Args:
            raw_text: The raw transcript text
            format_hint: Hint about the source format
            title: Optional title for the call
            call_date: Optional date of the call

        Returns:
            Parsed Transcript object
        """
        # Detect format if generic
        detected_format = self._detect_format(raw_text, format_hint)

        # Parse turns based on format
        turns = self._parse_turns(raw_text, detected_format)

        # Identify speakers
        speakers = self._identify_speakers(turns)

        # Calculate duration if timestamps available
        duration = self._calculate_duration(turns)

        return TranscriptData(
            id=str(uuid.uuid4()),
            title=title,
            format=detected_format,
            raw_text=raw_text,
            turns=turns,
            speakers=speakers,
            duration_minutes=duration,
            call_date=call_date,
            created_at=datetime.utcnow(),
        )

    def _detect_format(
        self,
        text: str,
        hint: TranscriptFormat,
    ) -> TranscriptFormat:
        """Detect the transcript format from the text.

        Args:
            text: Raw transcript text
            hint: Format hint from the user

        Returns:
            Detected TranscriptFormat
        """
        if hint != TranscriptFormat.GENERIC:
            return hint

        # Check for VTT format (Teams)
        if "WEBVTT" in text or "-->" in text:
            return TranscriptFormat.TEAMS

        # Check for Zoom format (HH:MM:SS at start of lines)
        if re.search(r"^\d{2}:\d{2}:\d{2}\s+\w+.*:", text, re.MULTILINE):
            return TranscriptFormat.ZOOM

        # Check for Avoma format (speaker then timestamp on separate lines)
        if re.search(
            r"^[A-Za-z].*\n\d{1,2}:\d{2}(?::\d{2})?\s*\n",
            text,
            re.MULTILINE,
        ):
            return TranscriptFormat.AVOMA

        return TranscriptFormat.GENERIC

    def _parse_turns(
        self,
        text: str,
        format: TranscriptFormat,
    ) -> list[TranscriptTurn]:
        """Parse conversation turns from the transcript.

        Args:
            text: Raw transcript text
            format: Detected format

        Returns:
            List of TranscriptTurn objects
        """
        turns: list[TranscriptTurn] = []

        # Select pattern based on format
        if format == TranscriptFormat.ZOOM:
            pattern = self.SPEAKER_PATTERNS["zoom"]
        elif format == TranscriptFormat.TEAMS:
            pattern = self.SPEAKER_PATTERNS["vtt"]
        elif format == TranscriptFormat.AVOMA:
            pattern = self.SPEAKER_PATTERNS["avoma"]
        else:
            # Try timestamped first, then colon format
            pattern = self.SPEAKER_PATTERNS["timestamped"]
            matches = list(pattern.finditer(text))
            if not matches:
                pattern = self.SPEAKER_PATTERNS["colon"]

        for match in pattern.finditer(text):
            groups = match.groupdict()

            speaker = groups.get("speaker", "Unknown").strip()
            turn_text = groups.get("text", "").strip()
            timestamp = groups.get("timestamp")

            if not turn_text:
                continue

            # Clean up multi-line text
            turn_text = " ".join(turn_text.split())

            turns.append(
                TranscriptTurn(
                    speaker=speaker,
                    text=turn_text,
                    timestamp=timestamp,
                    start_time=self._timestamp_to_seconds(timestamp),
                )
            )

        # If no turns found with patterns, try line-by-line parsing
        if not turns:
            turns = self._fallback_parse(text)

        return turns

    def _fallback_parse(self, text: str) -> list[TranscriptTurn]:
        """Fallback parser for unstructured transcripts.

        Args:
            text: Raw transcript text

        Returns:
            List of TranscriptTurn objects
        """
        turns: list[TranscriptTurn] = []
        current_speaker = "Unknown"

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if line starts with a speaker pattern
            colon_match = re.match(
                r"^([A-Za-z][A-Za-z\s\.,'()-]*?)(?:\s*\([^)]+\))?\s*:\s*(.+)$",
                line,
            )

            if colon_match:
                current_speaker = colon_match.group(1).strip()
                text_content = colon_match.group(2).strip()
            else:
                text_content = line

            if text_content:
                turns.append(
                    TranscriptTurn(
                        speaker=current_speaker,
                        text=text_content,
                    )
                )

        return turns

    def _identify_speakers(
        self,
        turns: list[TranscriptTurn],
    ) -> list[TranscriptSpeaker]:
        """Identify and classify speakers from the turns.

        Args:
            turns: List of transcript turns

        Returns:
            List of TranscriptSpeaker objects
        """
        speaker_names: set[str] = set()
        speakers: list[TranscriptSpeaker] = []

        for turn in turns:
            if turn.speaker not in speaker_names:
                speaker_names.add(turn.speaker)

                # Determine role
                role = self._classify_speaker_role(turn.speaker)

                speakers.append(
                    TranscriptSpeaker(
                        id=str(uuid.uuid4()),
                        name=turn.speaker,
                        role=role,
                    )
                )

        return speakers

    def _classify_speaker_role(self, speaker_name: str) -> str:
        """Classify a speaker's role based on their name.

        Args:
            speaker_name: The speaker's name

        Returns:
            Role classification ('sales_rep', 'prospect', or 'unknown')
        """
        name_lower = speaker_name.lower()

        # Check if this is the known sales rep
        if self.sales_rep_name:
            if self.sales_rep_name.lower() in name_lower:
                return "sales_rep"

        # Check for role indicators in parentheses or name
        for indicator in self.SALES_REP_INDICATORS:
            if indicator in name_lower:
                return "sales_rep"

        for indicator in self.PROSPECT_INDICATORS:
            if indicator in name_lower:
                return "prospect"

        return "unknown"

    def _timestamp_to_seconds(self, timestamp: Optional[str]) -> Optional[float]:
        """Convert timestamp string to seconds.

        Args:
            timestamp: Timestamp string (HH:MM:SS or MM:SS)

        Returns:
            Time in seconds or None
        """
        if not timestamp:
            return None

        parts = timestamp.replace(",", ".").split(":")
        try:
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
        except ValueError:
            return None

        return None

    def _calculate_duration(
        self,
        turns: list[TranscriptTurn],
    ) -> Optional[int]:
        """Calculate call duration from transcript turns.

        Args:
            turns: List of transcript turns

        Returns:
            Duration in minutes or None
        """
        if not turns:
            return None

        # Find last turn with timestamp
        last_time: Optional[float] = None
        for turn in reversed(turns):
            if turn.start_time is not None:
                last_time = turn.start_time
                break

        if last_time is not None:
            return int(last_time / 60) + 1

        return None

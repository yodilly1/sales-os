"""Transcript parsers for VTT and SRT formats."""

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.models.zoom import TranscriptLine, ParsedTranscript


class TranscriptParser(ABC):
    """Abstract base class for transcript parsers."""

    @abstractmethod
    def parse(self, content: str, meeting_id: str) -> ParsedTranscript:
        """Parse transcript content into structured format."""
        pass

    @staticmethod
    def extract_speaker(text: str) -> Tuple[Optional[str], str]:
        """Extract speaker name from text if present.

        Handles formats like:
        - "Speaker Name: Text..."
        - "<v Speaker Name>Text...</v>"
        """
        # VTT voice tag format: <v Speaker Name>text</v>
        voice_match = re.match(r"<v\s+([^>]+)>(.+?)(?:</v>)?$", text, re.DOTALL)
        if voice_match:
            return voice_match.group(1).strip(), voice_match.group(2).strip()

        # Colon format: Speaker Name: text
        colon_match = re.match(r"^([^:]{1,50}):\s*(.+)$", text, re.DOTALL)
        if colon_match:
            potential_speaker = colon_match.group(1).strip()
            # Only treat as speaker if it looks like a name (not a time or URL)
            if not re.match(r"^\d", potential_speaker) and "://" not in potential_speaker:
                return potential_speaker, colon_match.group(2).strip()

        return None, text


class VTTParser(TranscriptParser):
    """Parser for WebVTT (VTT) transcript format."""

    # VTT timestamp format: 00:00:00.000 or 00:00.000
    TIMESTAMP_PATTERN = re.compile(
        r"(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}:)?(\d{2}):(\d{2})\.(\d{3})"
    )

    def parse(self, content: str, meeting_id: str) -> ParsedTranscript:
        """Parse VTT content into structured format."""
        lines: List[TranscriptLine] = []
        speakers: set = set()
        total_duration = 0.0

        # Split content into blocks
        blocks = content.strip().split("\n\n")

        for block in blocks:
            block_lines = block.strip().split("\n")

            # Skip header block (WEBVTT)
            if block_lines[0].startswith("WEBVTT"):
                continue

            # Find timestamp line
            timestamp_line = None
            text_lines = []

            for line in block_lines:
                if self.TIMESTAMP_PATTERN.match(line):
                    timestamp_line = line
                elif timestamp_line and line.strip():
                    text_lines.append(line.strip())

            if timestamp_line and text_lines:
                start_time, end_time = self._parse_timestamp(timestamp_line)
                text = " ".join(text_lines)

                # Clean VTT tags
                text = self._clean_vtt_tags(text)

                # Extract speaker
                speaker, cleaned_text = self.extract_speaker(text)

                if speaker:
                    speakers.add(speaker)

                if cleaned_text:
                    lines.append(
                        TranscriptLine(
                            speaker=speaker,
                            start_time=start_time,
                            end_time=end_time,
                            text=cleaned_text,
                        )
                    )

                    if end_time > total_duration:
                        total_duration = end_time

        return ParsedTranscript(
            meeting_id=meeting_id,
            total_duration=total_duration,
            lines=lines,
            speakers=list(speakers),
            raw_text=self._build_raw_text(lines),
            format="vtt",
        )

    def _parse_timestamp(self, timestamp_line: str) -> Tuple[float, float]:
        """Parse VTT timestamp line into start and end seconds."""
        match = self.TIMESTAMP_PATTERN.match(timestamp_line)
        if not match:
            return 0.0, 0.0

        groups = match.groups()

        # Start time
        start_hours = int(groups[0].rstrip(":")) if groups[0] else 0
        start_minutes = int(groups[1])
        start_seconds = int(groups[2])
        start_millis = int(groups[3])
        start_time = start_hours * 3600 + start_minutes * 60 + start_seconds + start_millis / 1000

        # End time
        end_hours = int(groups[4].rstrip(":")) if groups[4] else 0
        end_minutes = int(groups[5])
        end_seconds = int(groups[6])
        end_millis = int(groups[7])
        end_time = end_hours * 3600 + end_minutes * 60 + end_seconds + end_millis / 1000

        return start_time, end_time

    def _clean_vtt_tags(self, text: str) -> str:
        """Remove VTT formatting tags from text."""
        # Remove <c> (class), <i> (italics), <b> (bold), <u> (underline) tags
        text = re.sub(r"</?[cibu][^>]*>", "", text)
        # Remove <lang> tags
        text = re.sub(r"</?lang[^>]*>", "", text)
        # Remove timing tags like <00:00:00.000>
        text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
        return text.strip()

    def _build_raw_text(self, lines: List[TranscriptLine]) -> str:
        """Build raw text from parsed lines."""
        return "\n".join(
            f"{line.speaker or 'Unknown'}: {line.text}" for line in lines
        )


class SRTParser(TranscriptParser):
    """Parser for SubRip (SRT) transcript format."""

    # SRT timestamp format: 00:00:00,000 --> 00:00:00,000
    TIMESTAMP_PATTERN = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )

    def parse(self, content: str, meeting_id: str) -> ParsedTranscript:
        """Parse SRT content into structured format."""
        lines: List[TranscriptLine] = []
        speakers: set = set()
        total_duration = 0.0

        # Split content into blocks (separated by blank lines)
        blocks = re.split(r"\n\s*\n", content.strip())

        for block in blocks:
            block_lines = block.strip().split("\n")

            if len(block_lines) < 3:
                continue

            # First line is the sequence number (skip it)
            # Second line is the timestamp
            # Remaining lines are the text

            timestamp_line = block_lines[1] if len(block_lines) > 1 else ""
            text_lines = block_lines[2:] if len(block_lines) > 2 else []

            match = self.TIMESTAMP_PATTERN.match(timestamp_line)
            if match and text_lines:
                start_time, end_time = self._parse_timestamp(match)
                text = " ".join(line.strip() for line in text_lines if line.strip())

                # Extract speaker
                speaker, cleaned_text = self.extract_speaker(text)

                if speaker:
                    speakers.add(speaker)

                if cleaned_text:
                    lines.append(
                        TranscriptLine(
                            speaker=speaker,
                            start_time=start_time,
                            end_time=end_time,
                            text=cleaned_text,
                        )
                    )

                    if end_time > total_duration:
                        total_duration = end_time

        return ParsedTranscript(
            meeting_id=meeting_id,
            total_duration=total_duration,
            lines=lines,
            speakers=list(speakers),
            raw_text=self._build_raw_text(lines),
            format="srt",
        )

    def _parse_timestamp(self, match: re.Match) -> Tuple[float, float]:
        """Parse SRT timestamp match into start and end seconds."""
        groups = match.groups()

        # Start time
        start_hours = int(groups[0])
        start_minutes = int(groups[1])
        start_seconds = int(groups[2])
        start_millis = int(groups[3])
        start_time = start_hours * 3600 + start_minutes * 60 + start_seconds + start_millis / 1000

        # End time
        end_hours = int(groups[4])
        end_minutes = int(groups[5])
        end_seconds = int(groups[6])
        end_millis = int(groups[7])
        end_time = end_hours * 3600 + end_minutes * 60 + end_seconds + end_millis / 1000

        return start_time, end_time

    def _build_raw_text(self, lines: List[TranscriptLine]) -> str:
        """Build raw text from parsed lines."""
        return "\n".join(
            f"{line.speaker or 'Unknown'}: {line.text}" for line in lines
        )


def get_parser(file_type: str) -> TranscriptParser:
    """Get the appropriate parser for a file type."""
    file_type = file_type.upper()
    if file_type in ("VTT", "WEBVTT"):
        return VTTParser()
    elif file_type == "SRT":
        return SRTParser()
    else:
        # Default to VTT parser
        return VTTParser()

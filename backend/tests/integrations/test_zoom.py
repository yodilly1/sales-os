"""Tests for Zoom integration."""

import pytest
from datetime import datetime

from app.integrations.zoom.parsers import VTTParser, SRTParser, get_parser
from app.integrations.zoom import ZoomClient
from app.models.zoom import (
    ZoomOAuthTokens,
    ZoomRecording,
    ZoomRecordingFile,
    TranscriptLine,
    ParsedTranscript,
)


class TestVTTParser:
    """Tests for VTT transcript parser."""

    def test_parse_basic_vtt(self):
        """Test parsing a basic VTT file."""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Speaker 1: Hello, how are you today?

00:00:05.000 --> 00:00:08.000
Speaker 2: I'm doing well, thanks for asking.

00:00:09.000 --> 00:00:12.000
Speaker 1: Let's discuss the project.
"""
        parser = VTTParser()
        result = parser.parse(vtt_content, "test-meeting-123")

        assert result.meeting_id == "test-meeting-123"
        assert len(result.lines) == 3
        assert result.format == "vtt"
        assert "Speaker 1" in result.speakers
        assert "Speaker 2" in result.speakers

    def test_parse_vtt_with_voice_tags(self):
        """Test parsing VTT with voice tags."""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
<v John Smith>Hello everyone.

00:00:05.000 --> 00:00:08.000
<v Jane Doe>Welcome to the meeting.
"""
        parser = VTTParser()
        result = parser.parse(vtt_content, "test-meeting-456")

        assert len(result.lines) == 2
        assert result.lines[0].speaker == "John Smith"
        assert result.lines[1].speaker == "Jane Doe"

    def test_parse_vtt_timestamps(self):
        """Test that timestamps are correctly parsed."""
        vtt_content = """WEBVTT

01:30:45.500 --> 01:30:50.250
Some text here.
"""
        parser = VTTParser()
        result = parser.parse(vtt_content, "test-meeting")

        assert len(result.lines) == 1
        # 1 hour + 30 min + 45.5 sec = 5445.5 seconds
        assert result.lines[0].start_time == 5445.5
        # 1 hour + 30 min + 50.25 sec = 5450.25 seconds
        assert result.lines[0].end_time == 5450.25

    def test_total_duration_calculation(self):
        """Test that total duration is calculated correctly."""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
First line.

00:00:10.000 --> 00:00:15.000
Second line.

00:00:20.000 --> 00:00:30.000
Third and final line.
"""
        parser = VTTParser()
        result = parser.parse(vtt_content, "test-meeting")

        assert result.total_duration == 30.0


class TestSRTParser:
    """Tests for SRT transcript parser."""

    def test_parse_basic_srt(self):
        """Test parsing a basic SRT file."""
        srt_content = """1
00:00:01,000 --> 00:00:04,000
Speaker 1: Hello, how are you?

2
00:00:05,000 --> 00:00:08,000
Speaker 2: I'm doing great.

3
00:00:09,000 --> 00:00:12,000
Speaker 1: Let's begin.
"""
        parser = SRTParser()
        result = parser.parse(srt_content, "test-meeting-srt")

        assert result.meeting_id == "test-meeting-srt"
        assert len(result.lines) == 3
        assert result.format == "srt"
        assert "Speaker 1" in result.speakers
        assert "Speaker 2" in result.speakers

    def test_parse_srt_timestamps(self):
        """Test SRT timestamp parsing with commas."""
        srt_content = """1
01:30:45,500 --> 01:30:50,250
Test content.
"""
        parser = SRTParser()
        result = parser.parse(srt_content, "test")

        assert len(result.lines) == 1
        assert result.lines[0].start_time == 5445.5
        assert result.lines[0].end_time == 5450.25


class TestGetParser:
    """Tests for parser factory function."""

    def test_get_vtt_parser(self):
        """Test getting VTT parser."""
        parser = get_parser("VTT")
        assert isinstance(parser, VTTParser)

        parser = get_parser("WEBVTT")
        assert isinstance(parser, VTTParser)

    def test_get_srt_parser(self):
        """Test getting SRT parser."""
        parser = get_parser("SRT")
        assert isinstance(parser, SRTParser)

    def test_default_parser(self):
        """Test that unknown types default to VTT."""
        parser = get_parser("UNKNOWN")
        assert isinstance(parser, VTTParser)


class TestTranscriptLine:
    """Tests for TranscriptLine model."""

    def test_transcript_line_creation(self):
        """Test creating a transcript line."""
        line = TranscriptLine(
            speaker="John Doe",
            start_time=10.5,
            end_time=15.0,
            text="Hello world",
        )

        assert line.speaker == "John Doe"
        assert line.start_time == 10.5
        assert line.end_time == 15.0
        assert line.text == "Hello world"

    def test_transcript_line_optional_speaker(self):
        """Test transcript line without speaker."""
        line = TranscriptLine(
            start_time=0.0,
            end_time=5.0,
            text="Unknown speaker text",
        )

        assert line.speaker is None
        assert line.text == "Unknown speaker text"


class TestParsedTranscript:
    """Tests for ParsedTranscript model."""

    def test_get_full_text(self):
        """Test getting full transcript as text."""
        transcript = ParsedTranscript(
            meeting_id="test-123",
            total_duration=60.0,
            lines=[
                TranscriptLine(
                    speaker="Alice",
                    start_time=0.0,
                    end_time=5.0,
                    text="Hello",
                ),
                TranscriptLine(
                    speaker="Bob",
                    start_time=5.0,
                    end_time=10.0,
                    text="Hi there",
                ),
            ],
            speakers=["Alice", "Bob"],
        )

        full_text = transcript.get_full_text()
        assert "Alice: Hello" in full_text
        assert "Bob: Hi there" in full_text


class TestZoomOAuthTokens:
    """Tests for ZoomOAuthTokens model."""

    def test_token_expiry_check(self):
        """Test token expiration check."""
        # Expired token
        expired_tokens = ZoomOAuthTokens(
            access_token="expired",
            refresh_token="refresh",
            expires_in=3600,
            scope="user:read",
            expires_at=datetime(2020, 1, 1),
        )
        assert expired_tokens.is_expired() is True

        # Valid token (future expiry)
        valid_tokens = ZoomOAuthTokens(
            access_token="valid",
            refresh_token="refresh",
            expires_in=3600,
            scope="user:read",
            expires_at=datetime(2099, 12, 31),
        )
        assert valid_tokens.is_expired() is False

    def test_token_without_expires_at(self):
        """Test that token without expires_at is considered expired."""
        tokens = ZoomOAuthTokens(
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
            scope="user:read",
        )
        assert tokens.is_expired() is True


class TestZoomWebhookValidation:
    """Tests for webhook signature validation."""

    def test_generate_webhook_response(self):
        """Test generating webhook validation response."""
        plain_token = "test-token-123"
        secret = "test-secret"

        response = ZoomClient.generate_webhook_response(plain_token, secret)

        assert "plainToken" in response
        assert "encryptedToken" in response
        assert response["plainToken"] == plain_token
        assert len(response["encryptedToken"]) == 64  # SHA256 hex

    def test_validate_webhook_signature(self):
        """Test webhook signature validation."""
        import json
        import hmac
        import hashlib

        payload = json.dumps({"event": "test"}).encode()
        timestamp = "1234567890"
        secret = "test-secret"

        # Generate valid signature
        message = f"v0:{timestamp}:{payload.decode('utf-8')}"
        expected_hash = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        valid_signature = f"v0={expected_hash}"

        # Should pass with valid signature
        assert ZoomClient.validate_webhook_signature(
            payload=payload,
            signature=valid_signature,
            timestamp=timestamp,
            secret=secret,
        ) is True

        # Should fail with invalid signature
        assert ZoomClient.validate_webhook_signature(
            payload=payload,
            signature="v0=invalid",
            timestamp=timestamp,
            secret=secret,
        ) is False


# Additional integration tests would go here, mocking the HTTP client
# for testing the full OAuth flow and API calls

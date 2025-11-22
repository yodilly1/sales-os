"""Custom exceptions for Zoom integration."""

from typing import Optional


class ZoomAPIError(Exception):
    """Base exception for Zoom API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ZoomAuthenticationError(ZoomAPIError):
    """Raised when authentication with Zoom fails."""

    def __init__(self, message: str = "Zoom authentication failed"):
        super().__init__(message, status_code=401)


class ZoomRateLimitError(ZoomAPIError):
    """Raised when Zoom API rate limit is exceeded."""

    def __init__(
        self, message: str = "Zoom API rate limit exceeded", retry_after: int = 60
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ZoomRecordingNotFoundError(ZoomAPIError):
    """Raised when a requested recording is not found."""

    def __init__(self, meeting_id: str):
        super().__init__(
            f"Recording not found for meeting {meeting_id}", status_code=404
        )
        self.meeting_id = meeting_id


class ZoomTranscriptNotFoundError(ZoomAPIError):
    """Raised when a transcript is not available for a recording."""

    def __init__(self, meeting_id: str):
        super().__init__(
            f"Transcript not available for meeting {meeting_id}", status_code=404
        )
        self.meeting_id = meeting_id


class ZoomTokenExpiredError(ZoomAuthenticationError):
    """Raised when the OAuth token has expired."""

    def __init__(self):
        super().__init__("Zoom OAuth token has expired")


class ZoomWebhookValidationError(ZoomAPIError):
    """Raised when webhook signature validation fails."""

    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message, status_code=403)

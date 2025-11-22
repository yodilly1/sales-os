"""
LinkedIn Integration Exceptions

Custom exceptions for handling LinkedIn API errors and edge cases.
"""

from typing import Optional


class LinkedInError(Exception):
    """Base exception for LinkedIn integration errors"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class LinkedInAuthError(LinkedInError):
    """Authentication or authorization error with LinkedIn API"""

    def __init__(
        self,
        message: str = "LinkedIn authentication failed",
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.status_code = 401


class LinkedInRateLimitError(LinkedInError):
    """Rate limit exceeded error"""

    def __init__(
        self,
        message: str = "LinkedIn API rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.retry_after = retry_after
        self.status_code = 429

    def __str__(self):
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after} seconds)"
        return base


class LinkedInNotFoundError(LinkedInError):
    """Resource not found error (profile or company doesn't exist)"""

    def __init__(
        self,
        message: str = "LinkedIn resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.status_code = 404

    def __str__(self):
        if self.resource_type and self.resource_id:
            return f"{self.resource_type} '{self.resource_id}' not found"
        return super().__str__()


class LinkedInAPIError(LinkedInError):
    """General API error from LinkedIn"""

    def __init__(
        self,
        message: str = "LinkedIn API error",
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.status_code = status_code


class LinkedInPrivacyError(LinkedInError):
    """Error when profile/data is private or restricted"""

    def __init__(
        self,
        message: str = "LinkedIn profile is private or restricted",
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.status_code = 403


class LinkedInValidationError(LinkedInError):
    """Validation error for LinkedIn data"""

    def __init__(
        self,
        message: str = "Invalid LinkedIn data",
        field: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.field = field
        self.status_code = 400

    def __str__(self):
        if self.field:
            return f"Validation error on field '{self.field}': {self.message}"
        return super().__str__()


class LinkedInConnectionError(LinkedInError):
    """Network/connection error when communicating with LinkedIn"""

    def __init__(
        self,
        message: str = "Failed to connect to LinkedIn",
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.status_code = 503


class LinkedInCacheError(LinkedInError):
    """Error related to caching LinkedIn data"""

    def __init__(
        self,
        message: str = "LinkedIn cache error",
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)

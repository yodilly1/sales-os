"""
HubSpot Integration Exceptions

Custom exception classes for handling HubSpot API errors and integration issues.
"""

from typing import Any


class HubSpotException(Exception):
    """Base exception for HubSpot integration errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        correlation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.correlation_id = correlation_id
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.correlation_id:
            parts.append(f"Correlation ID: {self.correlation_id}")
        return " | ".join(parts)


class HubSpotAuthenticationError(HubSpotException):
    """Raised when authentication with HubSpot fails."""

    def __init__(
        self,
        message: str = "Authentication failed with HubSpot API",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=401, **kwargs)


class HubSpotAuthorizationError(HubSpotException):
    """Raised when authorization is denied for a HubSpot operation."""

    def __init__(
        self,
        message: str = "Authorization denied for HubSpot operation",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=403, **kwargs)


class HubSpotNotFoundError(HubSpotException):
    """Raised when a requested resource is not found in HubSpot."""

    def __init__(
        self,
        message: str = "Resource not found in HubSpot",
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ):
        if resource_type and resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found in HubSpot"
        super().__init__(message, status_code=404, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class HubSpotValidationError(HubSpotException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Request validation failed",
        validation_errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=400, **kwargs)
        self.validation_errors = validation_errors or []


class HubSpotRateLimitError(HubSpotException):
    """Raised when HubSpot rate limit is exceeded."""

    def __init__(
        self,
        message: str = "HubSpot API rate limit exceeded",
        retry_after: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class HubSpotConflictError(HubSpotException):
    """Raised when there's a conflict (e.g., duplicate contact)."""

    def __init__(
        self,
        message: str = "Resource conflict in HubSpot",
        existing_id: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=409, **kwargs)
        self.existing_id = existing_id


class HubSpotServerError(HubSpotException):
    """Raised when HubSpot API returns a server error."""

    def __init__(
        self,
        message: str = "HubSpot API server error",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=500, **kwargs)


class HubSpotConnectionError(HubSpotException):
    """Raised when connection to HubSpot API fails."""

    def __init__(
        self,
        message: str = "Failed to connect to HubSpot API",
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)


class HubSpotTokenExpiredError(HubSpotException):
    """Raised when OAuth token has expired and refresh fails."""

    def __init__(
        self,
        message: str = "HubSpot OAuth token expired and could not be refreshed",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=401, **kwargs)


class HubSpotConfigurationError(HubSpotException):
    """Raised when HubSpot client is not properly configured."""

    def __init__(
        self,
        message: str = "HubSpot client is not properly configured",
        missing_fields: list[str] | None = None,
        **kwargs: Any,
    ):
        if missing_fields:
            message = f"{message}. Missing: {', '.join(missing_fields)}"
        super().__init__(message, **kwargs)
        self.missing_fields = missing_fields or []

"""Custom exceptions for the application."""


class SalesOSException(Exception):
    """Base exception for Sales OS."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SalesOSException):
    """Validation error."""

    pass


class ExportError(SalesOSException):
    """Export operation error."""

    pass


class ImportError(SalesOSException):
    """Import operation error."""

    pass


class FileNotFoundError(SalesOSException):
    """File not found error."""

    pass


class UnsupportedFormatError(SalesOSException):
    """Unsupported file format error."""

    pass


class JobNotFoundError(SalesOSException):
    """Background job not found."""

    pass


class JobCancelledError(SalesOSException):
    """Background job was cancelled."""

    pass


class AuthenticationError(SalesOSException):
    """Authentication failed."""

    pass


class AuthorizationError(SalesOSException):
    """Authorization denied."""

    pass


class RateLimitError(SalesOSException):
    """Rate limit exceeded."""

    pass


class ExternalServiceError(SalesOSException):
    """External service (HubSpot, Avoma, etc.) error."""

    pass

"""Error handling utilities for the enrichment service."""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Optional, Type

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class EnrichmentError(Exception):
    """Base exception for enrichment service errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EnrichmentError):
    """Exception for validation errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)


class ProviderError(EnrichmentError):
    """Exception for enrichment provider errors."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: Optional[dict] = None,
    ):
        details = details or {}
        details["provider"] = provider
        super().__init__(message, status_code=502, details=details)


class RateLimitError(EnrichmentError):
    """Exception for rate limit errors."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
    ):
        super().__init__(
            message,
            status_code=429,
            details={"retry_after": retry_after},
        )


class NotFoundError(EnrichmentError):
    """Exception for resource not found errors."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class ConfigurationError(EnrichmentError):
    """Exception for configuration errors."""

    def __init__(self, message: str, missing_config: Optional[list[str]] = None):
        super().__init__(
            message,
            status_code=503,
            details={"missing_config": missing_config or []},
        )


async def error_handler(request: Request, call_next: Callable) -> JSONResponse:
    """
    Global error handler middleware.

    Catches and formats all exceptions into consistent JSON responses.
    """
    try:
        return await call_next(request)
    except EnrichmentError as e:
        logger.warning(f"Enrichment error: {e.message}", extra={"details": e.details})
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": type(e).__name__,
                "message": e.message,
                "details": e.details,
            },
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "HTTPException",
                "message": e.detail,
            },
        )
    except PydanticValidationError as e:
        logger.warning(f"Validation error: {e}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": e.errors(),
            },
        )
    except Exception as e:
        logger.error(
            f"Unhandled error: {e}",
            exc_info=True,
            extra={"traceback": traceback.format_exc()},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalError",
                "message": "An unexpected error occurred",
            },
        )


def handle_provider_errors(provider_name: str):
    """
    Decorator to handle provider-specific errors.

    Usage:
        @handle_provider_errors("clearbit")
        async def fetch_from_clearbit():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ProviderError:
                raise
            except Exception as e:
                logger.error(f"Provider {provider_name} error: {e}", exc_info=True)
                raise ProviderError(
                    provider=provider_name,
                    message=f"Error communicating with {provider_name}",
                    details={"original_error": str(e)},
                )

        return wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator to retry function on specified exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch

    Usage:
        @retry_on_error(max_retries=3, exceptions=(ConnectionError,))
        async def unreliable_api_call():
            pass
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed: {e}")

            raise last_exception

        return wrapper

    return decorator


class ErrorCollector:
    """Collects errors during batch processing."""

    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def add_error(
        self,
        message: str,
        item_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Add an error to the collection."""
        self.errors.append({
            "message": message,
            "item_id": item_id,
            "details": details or {},
        })

    def add_warning(
        self,
        message: str,
        item_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Add a warning to the collection."""
        self.warnings.append({
            "message": message,
            "item_id": item_id,
            "details": details or {},
        })

    @property
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were collected."""
        return len(self.warnings) > 0

    def get_summary(self) -> dict:
        """Get summary of collected errors and warnings."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }

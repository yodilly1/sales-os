"""Activity logging middleware for automatic request/response logging."""

import logging
import time
import uuid
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.models.activity import ActivityCategory, ActivitySeverity
from app.services.activity.activity_service import ActivityService

logger = logging.getLogger(__name__)
settings = get_settings()


# Paths to exclude from automatic logging
EXCLUDED_PATHS = [
    "/health",
    "/healthz",
    "/ready",
    "/readyz",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
]

# Paths with sensitive data that should have limited logging
SENSITIVE_PATHS = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/password",
]


def get_client_ip(request: Request) -> str | None:
    """Extract client IP address from request.

    Handles X-Forwarded-For and X-Real-IP headers for proxy scenarios.

    Args:
        request: The incoming request

    Returns:
        Client IP address or None
    """
    # Check X-Forwarded-For header (may contain multiple IPs)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return None


def categorize_request(method: str, path: str) -> ActivityCategory:
    """Determine the activity category based on request method and path.

    Args:
        method: HTTP method
        path: Request path

    Returns:
        Appropriate activity category
    """
    path_lower = path.lower()

    # Authentication endpoints
    if "/auth/login" in path_lower:
        return ActivityCategory.USER_LOGIN
    if "/auth/logout" in path_lower:
        return ActivityCategory.USER_LOGOUT

    # Transcript endpoints
    if "/transcript" in path_lower:
        if method == "POST":
            return ActivityCategory.TRANSCRIPT_UPLOAD
        if "analyze" in path_lower or "spiced" in path_lower:
            return ActivityCategory.TRANSCRIPT_SPICED_ANALYSIS
        if method == "DELETE":
            return ActivityCategory.TRANSCRIPT_DELETE
        return ActivityCategory.TRANSCRIPT_PROCESS

    # Content endpoints
    if "/content" in path_lower:
        if method == "POST" and "generate" in path_lower:
            return ActivityCategory.CONTENT_GENERATE
        if "deck" in path_lower:
            return ActivityCategory.CONTENT_DECK_CREATE
        if "proposal" in path_lower:
            return ActivityCategory.CONTENT_PROPOSAL_CREATE
        if "export" in path_lower:
            return ActivityCategory.CONTENT_EXPORT
        if method == "DELETE":
            return ActivityCategory.CONTENT_DELETE
        return ActivityCategory.CONTENT_GENERATE

    # CRM endpoints
    if "/crm" in path_lower or "/hubspot" in path_lower or "/salesforce" in path_lower:
        if "sync" in path_lower:
            return ActivityCategory.CRM_SYNC_START
        if "/contact" in path_lower:
            return ActivityCategory.CRM_CONTACT_CREATE if method == "POST" else ActivityCategory.CRM_CONTACT_UPDATE
        if "/deal" in path_lower:
            return ActivityCategory.CRM_DEAL_CREATE if method == "POST" else ActivityCategory.CRM_DEAL_UPDATE
        return ActivityCategory.INTEGRATION_HUBSPOT_SYNC

    # Integration endpoints
    if "/integration" in path_lower or "/webhook" in path_lower:
        if "avoma" in path_lower:
            return ActivityCategory.INTEGRATION_AVOMA_SYNC
        if "webhook" in path_lower:
            return ActivityCategory.INTEGRATION_WEBHOOK_RECEIVED
        if method == "POST":
            return ActivityCategory.INTEGRATION_CONNECT
        if method == "DELETE":
            return ActivityCategory.INTEGRATION_DISCONNECT
        return ActivityCategory.INTEGRATION_CONNECT

    # Coaching endpoints
    if "/coaching" in path_lower:
        return ActivityCategory.COACHING_REPORT_GENERATE

    # User endpoints
    if "/user" in path_lower or "/profile" in path_lower:
        if "/settings" in path_lower:
            return ActivityCategory.USER_SETTINGS_CHANGE
        if "/password" in path_lower:
            return ActivityCategory.USER_PASSWORD_CHANGE
        return ActivityCategory.USER_PROFILE_UPDATE

    # Default to API request
    return ActivityCategory.API_REQUEST


def determine_severity(status_code: int) -> ActivitySeverity:
    """Determine severity based on HTTP status code.

    Args:
        status_code: HTTP response status code

    Returns:
        Appropriate severity level
    """
    if status_code >= 500:
        return ActivitySeverity.ERROR
    if status_code >= 400:
        return ActivitySeverity.WARNING
    if status_code >= 300:
        return ActivitySeverity.INFO
    return ActivitySeverity.INFO


class ActivityLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that automatically logs all API requests and responses."""

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: list[str] | None = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            excluded_paths: Paths to exclude from logging
            log_request_body: Whether to log request bodies (use with caution)
            log_response_body: Whether to log response bodies (use with caution)
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or EXCLUDED_PATHS
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process the request and log activity.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the handler
        """
        # Check if logging is enabled
        if not settings.ACTIVITY_LOG_ENABLED:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store request ID in state for use by handlers
        request.state.request_id = request_id

        # Capture request details
        start_time = time.perf_counter()
        method = request.method
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")

        # Extract user info if available (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)
        organization_id = getattr(request.state, "organization_id", None)

        # Execute the request
        response: Response | None = None
        error_message: str | None = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            logger.exception("Request failed: %s", e)
            raise
        finally:
            # Calculate response time
            end_time = time.perf_counter()
            response_time_ms = int((end_time - start_time) * 1000)

            # Determine category and severity
            category = categorize_request(method, path)
            severity = determine_severity(status_code)

            if error_message:
                severity = ActivitySeverity.ERROR

            # Build action description
            action = f"{method} {path}"
            if status_code >= 400:
                action = f"{action} failed with status {status_code}"

            # Prepare details
            details: dict[str, Any] = {
                "response_time_ms": response_time_ms,
            }

            # Add query params (excluding sensitive data)
            if request.query_params:
                safe_params = {
                    k: v
                    for k, v in request.query_params.items()
                    if k.lower() not in ["password", "token", "secret", "key", "api_key"]
                }
                if safe_params:
                    details["query_params"] = safe_params

            # Log the activity asynchronously
            try:
                async with async_session_maker() as session:
                    activity_service = ActivityService(session)
                    await activity_service.log_activity(
                        category=category,
                        action=action,
                        user_id=user_id,
                        user_email=user_email,
                        organization_id=organization_id,
                        severity=severity,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        request_id=request_id,
                        request_method=method,
                        request_path=path,
                        status_code=status_code,
                        response_time_ms=response_time_ms,
                        details=details if details else None,
                        error_message=error_message,
                    )
                    await session.commit()
            except Exception as log_error:
                # Don't let logging failures affect the request
                logger.error("Failed to log activity: %s", log_error)

        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware that sets up request context for activity logging."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Add request context for logging.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the handler
        """
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Initialize user context (will be set by auth middleware)
        request.state.user_id = None
        request.state.user_email = None
        request.state.organization_id = None

        response = await call_next(request)

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id

        return response

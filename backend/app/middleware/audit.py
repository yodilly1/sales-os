"""Audit logging middleware."""

import uuid
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import AuditAction
from app.core.security import get_client_ip
from app.models.audit_log import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of requests."""

    # Endpoints to audit automatically
    AUDITED_PATHS = {
        "/api/auth/login": AuditAction.LOGIN,
        "/api/auth/logout": AuditAction.LOGOUT,
        "/api/auth/refresh": AuditAction.TOKEN_REFRESH,
    }

    # Methods to audit
    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log if applicable."""
        # Skip if audit logging is disabled
        if not settings.audit_log_enabled:
            return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Check if this request should be audited
        should_audit = (
            request.url.path in self.AUDITED_PATHS
            or request.method in self.AUDITED_METHODS
        )

        if should_audit:
            # Schedule async audit log creation
            # Note: In production, use background tasks or message queue
            await self._create_audit_log(request, response)

        return response

    async def _create_audit_log(
        self,
        request: Request,
        response: Response,
    ) -> None:
        """Create audit log entry."""
        # This is a simplified version - in production, use background tasks
        # to avoid blocking the response
        pass  # Actual logging is done via AuditLogger service


class AuditLogger:
    """Service for creating audit log entries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: AuditAction,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: The action being logged
            user_id: The user performing the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            request: Optional request object for IP/UA extraction
            details: Additional details to log
            status: Status of the action (success/failure)

        Returns:
            Created AuditLog entry
        """
        ip_address = None
        user_agent = None

        if request:
            ip_address = get_client_ip(
                x_forwarded_for=request.headers.get("X-Forwarded-For"),
                x_real_ip=request.headers.get("X-Real-IP"),
                remote_addr=request.client.host if request.client else None,
            )
            user_agent = request.headers.get("User-Agent")

        audit_log = AuditLog(
            user_id=user_id,
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status=status,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def log_login(
        self,
        user_id: uuid.UUID,
        request: Request,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a login attempt."""
        return await self.log(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            user_id=user_id if success else None,
            resource_type="user",
            resource_id=str(user_id),
            request=request,
            details=details,
            status="success" if success else "failure",
        )

    async def log_logout(
        self,
        user_id: uuid.UUID,
        request: Request,
    ) -> AuditLog:
        """Log a logout."""
        return await self.log(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id),
            request=request,
        )

    async def log_api_key_created(
        self,
        user_id: uuid.UUID,
        api_key_id: uuid.UUID,
        request: Request,
        key_name: str,
    ) -> AuditLog:
        """Log API key creation."""
        return await self.log(
            action=AuditAction.API_KEY_CREATED,
            user_id=user_id,
            resource_type="api_key",
            resource_id=str(api_key_id),
            request=request,
            details={"key_name": key_name},
        )

    async def log_api_key_revoked(
        self,
        user_id: uuid.UUID,
        api_key_id: uuid.UUID,
        request: Request,
    ) -> AuditLog:
        """Log API key revocation."""
        return await self.log(
            action=AuditAction.API_KEY_REVOKED,
            user_id=user_id,
            resource_type="api_key",
            resource_id=str(api_key_id),
            request=request,
        )

    async def log_oauth_connected(
        self,
        user_id: uuid.UUID,
        provider: str,
        request: Request,
    ) -> AuditLog:
        """Log OAuth provider connection."""
        return await self.log(
            action=AuditAction.OAUTH_CONNECTED,
            user_id=user_id,
            resource_type="oauth",
            resource_id=provider,
            request=request,
            details={"provider": provider},
        )

    async def log_oauth_disconnected(
        self,
        user_id: uuid.UUID,
        provider: str,
        request: Request,
    ) -> AuditLog:
        """Log OAuth provider disconnection."""
        return await self.log(
            action=AuditAction.OAUTH_DISCONNECTED,
            user_id=user_id,
            resource_type="oauth",
            resource_id=provider,
            request=request,
            details={"provider": provider},
        )

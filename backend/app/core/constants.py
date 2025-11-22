"""Application constants."""

from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    MANAGER = "manager"
    REP = "rep"
    VIEWER = "viewer"


class TokenType(str, Enum):
    """Token types for JWT."""

    ACCESS = "access"
    REFRESH = "refresh"


class AuditAction(str, Enum):
    """Audit log action types."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    OAUTH_CONNECTED = "oauth_connected"
    OAUTH_DISCONNECTED = "oauth_disconnected"
    TRANSCRIPT_UPLOADED = "transcript_uploaded"
    CONTENT_GENERATED = "content_generated"
    PROSPECT_ENRICHED = "prospect_enriched"
    COACHING_GENERATED = "coaching_generated"


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    HUBSPOT = "hubspot"
    AVOMA = "avoma"


# API Key settings
API_KEY_HEADER = "X-API-Key"
API_KEY_QUERY_PARAM = "api_key"

# JWT settings
JWT_BEARER_SCHEME = "Bearer"

# Rate limiting
DEFAULT_RATE_LIMIT = "100/minute"
AUTH_RATE_LIMIT = "10/minute"

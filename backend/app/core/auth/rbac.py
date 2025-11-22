"""Role-Based Access Control (RBAC) implementation."""

from enum import Enum
from functools import wraps
from typing import Callable, List, Optional, Set

from app.core.constants import UserRole


class Permission(str, Enum):
    """System permissions."""

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"

    # Team management
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE_MEMBERS = "team:manage_members"

    # Organization management
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_MANAGE_SETTINGS = "org:manage_settings"

    # Transcript management
    TRANSCRIPT_CREATE = "transcript:create"
    TRANSCRIPT_READ = "transcript:read"
    TRANSCRIPT_READ_ALL = "transcript:read_all"
    TRANSCRIPT_DELETE = "transcript:delete"

    # Content management
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_TEMPLATE_MANAGE = "content:template_manage"

    # Coaching
    COACHING_READ = "coaching:read"
    COACHING_READ_ALL = "coaching:read_all"
    COACHING_SETTINGS = "coaching:settings"

    # Integrations
    INTEGRATION_MANAGE = "integration:manage"
    INTEGRATION_READ = "integration:read"

    # API Keys
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_DELETE = "api_key:delete"

    # Audit Logs
    AUDIT_LOG_READ = "audit_log:read"

    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_READ_ALL = "analytics:read_all"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: set(Permission),  # Admins have all permissions
    UserRole.MANAGER: {
        # User management (limited)
        Permission.USER_READ,
        Permission.USER_LIST,
        # Team management
        Permission.TEAM_READ,
        Permission.TEAM_UPDATE,
        Permission.TEAM_MANAGE_MEMBERS,
        # Organization (read only)
        Permission.ORG_READ,
        # Transcripts (all)
        Permission.TRANSCRIPT_CREATE,
        Permission.TRANSCRIPT_READ,
        Permission.TRANSCRIPT_READ_ALL,
        # Content
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_TEMPLATE_MANAGE,
        # Coaching (all)
        Permission.COACHING_READ,
        Permission.COACHING_READ_ALL,
        Permission.COACHING_SETTINGS,
        # Integrations
        Permission.INTEGRATION_READ,
        # API Keys (own)
        Permission.API_KEY_CREATE,
        Permission.API_KEY_READ,
        Permission.API_KEY_DELETE,
        # Analytics (all)
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_READ_ALL,
    },
    UserRole.REP: {
        # User (own profile)
        Permission.USER_READ,
        # Team (read only)
        Permission.TEAM_READ,
        # Organization (read only)
        Permission.ORG_READ,
        # Transcripts (own)
        Permission.TRANSCRIPT_CREATE,
        Permission.TRANSCRIPT_READ,
        # Content (own)
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        # Coaching (own)
        Permission.COACHING_READ,
        # Integrations (read only)
        Permission.INTEGRATION_READ,
        # API Keys (own)
        Permission.API_KEY_CREATE,
        Permission.API_KEY_READ,
        Permission.API_KEY_DELETE,
        # Analytics (own)
        Permission.ANALYTICS_READ,
    },
    UserRole.VIEWER: {
        # Read-only access
        Permission.USER_READ,
        Permission.TEAM_READ,
        Permission.ORG_READ,
        Permission.TRANSCRIPT_READ,
        Permission.CONTENT_READ,
        Permission.COACHING_READ,
        Permission.INTEGRATION_READ,
        Permission.ANALYTICS_READ,
    },
}


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: The user role

    Returns:
        Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(roles: List[str]) -> Set[Permission]:
    """
    Get all permissions for a user based on their roles.

    Args:
        roles: List of role strings

    Returns:
        Combined set of permissions from all roles
    """
    permissions: Set[Permission] = set()

    for role_str in roles:
        try:
            role = UserRole(role_str)
            permissions.update(get_role_permissions(role))
        except ValueError:
            # Ignore invalid roles
            continue

    return permissions


def has_permission(roles: List[str], permission: Permission) -> bool:
    """
    Check if a user with given roles has a permission.

    Args:
        roles: List of user role strings
        permission: The permission to check

    Returns:
        True if user has the permission
    """
    user_permissions = get_user_permissions(roles)
    return permission in user_permissions


def has_any_permission(roles: List[str], permissions: List[Permission]) -> bool:
    """
    Check if a user has any of the given permissions.

    Args:
        roles: List of user role strings
        permissions: List of permissions to check

    Returns:
        True if user has at least one permission
    """
    user_permissions = get_user_permissions(roles)
    return bool(user_permissions & set(permissions))


def has_all_permissions(roles: List[str], permissions: List[Permission]) -> bool:
    """
    Check if a user has all of the given permissions.

    Args:
        roles: List of user role strings
        permissions: List of permissions to check

    Returns:
        True if user has all permissions
    """
    user_permissions = get_user_permissions(roles)
    return set(permissions).issubset(user_permissions)


def is_admin(roles: List[str]) -> bool:
    """Check if user has admin role."""
    return UserRole.ADMIN.value in roles


def is_manager_or_above(roles: List[str]) -> bool:
    """Check if user has manager or admin role."""
    return UserRole.ADMIN.value in roles or UserRole.MANAGER.value in roles


class RBACChecker:
    """RBAC checker for use in FastAPI dependencies."""

    def __init__(
        self,
        required_permissions: Optional[List[Permission]] = None,
        require_all: bool = True,
        allowed_roles: Optional[List[UserRole]] = None,
    ):
        """
        Initialize RBAC checker.

        Args:
            required_permissions: List of required permissions
            require_all: If True, all permissions required; if False, any one is sufficient
            allowed_roles: Optional list of allowed roles (bypasses permission check)
        """
        self.required_permissions = required_permissions or []
        self.require_all = require_all
        self.allowed_roles = allowed_roles or []

    def check(self, roles: List[str]) -> bool:
        """
        Check if roles satisfy the requirements.

        Args:
            roles: List of user role strings

        Returns:
            True if requirements are satisfied
        """
        # Check allowed roles first
        if self.allowed_roles:
            for role in roles:
                try:
                    if UserRole(role) in self.allowed_roles:
                        return True
                except ValueError:
                    continue

        # Check permissions
        if not self.required_permissions:
            return True

        if self.require_all:
            return has_all_permissions(roles, self.required_permissions)
        else:
            return has_any_permission(roles, self.required_permissions)

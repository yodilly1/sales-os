<<<<<<< HEAD
<<<<<<< HEAD
"""Authentication and authorization modules."""

from app.core.auth.tokens import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    TokenPayload,
)
from app.core.auth.password import (
    hash_password,
    verify_password,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    "TokenPayload",
    "hash_password",
    "verify_password",
]
=======
"""Authentication and authorization utilities."""

# Placeholder for auth middleware integration
# Will be implemented by AGENT-012 (security/auth)


async def get_current_user():
    """Get current authenticated user.

    This is a placeholder that will be implemented by the auth agent.
    Returns None until proper authentication is set up.
    """
    return None


async def get_current_user_optional():
    """Get current user if authenticated, otherwise None.

    This is a placeholder that will be implemented by the auth agent.
    """
    return None
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
=======
"""Authentication and authorization utilities."""
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP

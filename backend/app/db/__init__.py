<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""Database configuration and utilities.

This module will be fully implemented by AGENT-011 for database schema setup.
"""
=======
"""Database configuration and session management."""

from app.db.base import Base
from app.db.session import get_db, engine, AsyncSessionLocal

__all__ = ["Base", "get_db", "engine", "AsyncSessionLocal"]
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
=======
"""Database configuration and session management."""

from app.db.base import Base
from app.db.session import (
    async_session_maker,
    engine,
    get_db,
    init_db,
)

__all__ = [
    "Base",
    "async_session_maker",
    "engine",
    "get_db",
    "init_db",
]
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
=======
# Database module
from app.db.base import Base
from app.db.session import get_db, AsyncSessionLocal, engine

__all__ = ["Base", "get_db", "AsyncSessionLocal", "engine"]
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
=======
"""Database configuration and utilities."""
>>>>>>> origin/claude/zoom-integration-01Dy2JADoQefKcjQi2GPsjPP

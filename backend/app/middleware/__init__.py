"""Middleware components for Sales OS."""

from app.middleware.activity_logger import ActivityLoggerMiddleware

__all__ = [
    "ActivityLoggerMiddleware",
]

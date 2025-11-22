"""Core configuration and utilities for Sales OS backend."""

from .config import settings
from .database import get_db, engine, SessionLocal

__all__ = ["settings", "get_db", "engine", "SessionLocal"]

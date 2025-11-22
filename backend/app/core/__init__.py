"""
Core Configuration and Utilities for Sales OS
"""

from .config import Settings, EmailSettings, get_settings, get_email_config

__all__ = [
    "Settings",
    "EmailSettings",
    "get_settings",
    "get_email_config",
]

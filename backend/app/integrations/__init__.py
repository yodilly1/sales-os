"""
External service integrations for Sales OS.
"""

from .avoma import AvomaClient, AvomaAuthManager

__all__ = ["AvomaClient", "AvomaAuthManager"]

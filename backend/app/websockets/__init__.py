"""
WebSocket module for real-time communication.

This package provides WebSocket connection management and message
handling for real-time notification delivery.
"""

from .manager import WebSocketManager, websocket_manager, ConnectionInfo

__all__ = [
    "WebSocketManager",
    "websocket_manager",
    "ConnectionInfo",
]

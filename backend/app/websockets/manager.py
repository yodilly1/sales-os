"""
WebSocket connection manager for real-time notifications.

This module provides a WebSocket connection manager that handles
multiple client connections and broadcasts notifications in real-time.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..models.notification import (
    NotificationResponse,
    WebSocketNotificationEvent,
    WebSocketConnectionEvent,
    WebSocketHeartbeat,
)

logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""

    user_id: str
    organization_id: Optional[str] = None
    connected_at: datetime
    last_heartbeat: datetime


class WebSocketManager:
    """
    Manager for WebSocket connections.

    Handles connection lifecycle, message broadcasting, and heartbeat
    monitoring for real-time notification delivery.
    """

    def __init__(self, heartbeat_interval: int = 30, connection_timeout: int = 120):
        """
        Initialize the WebSocket manager.

        Args:
            heartbeat_interval: Seconds between heartbeat messages
            connection_timeout: Seconds before a connection is considered dead
        """
        # Map of user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

        # Map of WebSocket -> ConnectionInfo
        self._connection_info: Dict[WebSocket, ConnectionInfo] = {}

        # Heartbeat configuration
        self._heartbeat_interval = heartbeat_interval
        self._connection_timeout = connection_timeout

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the background tasks for heartbeat and cleanup."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop background tasks and close all connections."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Close all connections
        async with self._lock:
            for websocket in list(self._connection_info.keys()):
                try:
                    await websocket.close()
                except Exception:
                    pass

            self._connections.clear()
            self._connection_info.clear()

        logger.info("WebSocket manager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: The authenticated user's ID
            organization_id: Optional organization ID
        """
        await websocket.accept()

        now = datetime.utcnow()
        connection_info = ConnectionInfo(
            user_id=user_id,
            organization_id=organization_id,
            connected_at=now,
            last_heartbeat=now,
        )

        async with self._lock:
            # Add to user's connection set
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)

            # Store connection info
            self._connection_info[websocket] = connection_info

        logger.info(f"WebSocket connected for user {user_id}")

        # Send connection confirmation
        await self._send_message(
            websocket,
            WebSocketConnectionEvent(
                status="connected",
                user_id=UUID(user_id),
                timestamp=now,
            ),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Handle a WebSocket disconnection.

        Args:
            websocket: The WebSocket connection to disconnect
        """
        async with self._lock:
            info = self._connection_info.pop(websocket, None)
            if info:
                user_id = info.user_id
                if user_id in self._connections:
                    self._connections[user_id].discard(websocket)
                    if not self._connections[user_id]:
                        del self._connections[user_id]
                logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_notification(
        self, user_id: str, notification: NotificationResponse
    ) -> bool:
        """
        Send a notification to a specific user.

        Args:
            user_id: The user ID to send to
            notification: The notification to send

        Returns:
            True if sent to at least one connection, False otherwise
        """
        event = WebSocketNotificationEvent(notification=notification)
        return await self._broadcast_to_user(user_id, event)

    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Send arbitrary data to a specific user.

        Args:
            user_id: The user ID to send to
            data: The data to send

        Returns:
            True if sent to at least one connection, False otherwise
        """
        async with self._lock:
            connections = self._connections.get(user_id, set()).copy()

        if not connections:
            logger.debug(f"No active connections for user {user_id}")
            return False

        sent = False
        for websocket in connections:
            try:
                await websocket.send_json(data)
                sent = True
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                await self.disconnect(websocket)

        return sent

    async def broadcast_to_organization(
        self, organization_id: str, data: Dict[str, Any]
    ) -> int:
        """
        Broadcast data to all users in an organization.

        Args:
            organization_id: The organization ID
            data: The data to broadcast

        Returns:
            Number of users who received the message
        """
        async with self._lock:
            target_websockets = [
                ws
                for ws, info in self._connection_info.items()
                if info.organization_id == organization_id
            ]

        sent_count = 0
        for websocket in target_websockets:
            try:
                await websocket.send_json(data)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast to organization: {e}")
                await self.disconnect(websocket)

        return sent_count

    async def broadcast_all(self, data: Dict[str, Any]) -> int:
        """
        Broadcast data to all connected users.

        Args:
            data: The data to broadcast

        Returns:
            Number of connections that received the message
        """
        async with self._lock:
            all_websockets = list(self._connection_info.keys())

        sent_count = 0
        for websocket in all_websockets:
            try:
                await websocket.send_json(data)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast: {e}")
                await self.disconnect(websocket)

        return sent_count

    async def handle_message(
        self, websocket: WebSocket, message: Dict[str, Any]
    ) -> None:
        """
        Handle an incoming WebSocket message.

        Args:
            websocket: The WebSocket connection
            message: The received message
        """
        message_type = message.get("type")

        if message_type == "heartbeat":
            # Update last heartbeat time
            async with self._lock:
                if websocket in self._connection_info:
                    self._connection_info[websocket].last_heartbeat = datetime.utcnow()

            # Respond with heartbeat
            await self._send_message(websocket, WebSocketHeartbeat())

        elif message_type == "subscribe":
            # Handle subscription requests (future use)
            pass

        elif message_type == "unsubscribe":
            # Handle unsubscription requests (future use)
            pass

    async def _broadcast_to_user(self, user_id: str, event: BaseModel) -> bool:
        """Broadcast an event to all connections of a specific user."""
        async with self._lock:
            connections = self._connections.get(user_id, set()).copy()

        if not connections:
            return False

        sent = False
        for websocket in connections:
            try:
                await self._send_message(websocket, event)
                sent = True
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                await self.disconnect(websocket)

        return sent

    async def _send_message(self, websocket: WebSocket, message: BaseModel) -> None:
        """Send a Pydantic model as JSON to a WebSocket."""
        await websocket.send_json(message.model_dump(mode="json"))

    async def _heartbeat_loop(self) -> None:
        """Background task to send periodic heartbeats."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                heartbeat = WebSocketHeartbeat()

                async with self._lock:
                    websockets = list(self._connection_info.keys())

                for websocket in websockets:
                    try:
                        await self._send_message(websocket, heartbeat)
                    except Exception:
                        await self.disconnect(websocket)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _cleanup_loop(self) -> None:
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(self._connection_timeout // 2)
                now = datetime.utcnow()

                async with self._lock:
                    stale = [
                        ws
                        for ws, info in self._connection_info.items()
                        if (now - info.last_heartbeat).total_seconds() > self._connection_timeout
                    ]

                for websocket in stale:
                    logger.info("Cleaning up stale WebSocket connection")
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                    await self.disconnect(websocket)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self._connection_info)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get the number of active connections for a specific user."""
        return len(self._connections.get(user_id, set()))

    def get_connected_users(self) -> Set[str]:
        """Get the set of currently connected user IDs."""
        return set(self._connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

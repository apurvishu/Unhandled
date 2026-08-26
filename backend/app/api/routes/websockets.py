"""WebSocket endpoints for live vessel positions, notifications, and alerts."""

import json
from typing import Dict, List
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_token
from app.utils.logging import get_logger

logger = get_logger("websockets")

router = APIRouter(prefix="/ws")


class ConnectionManager:
    """Manages active WebSocket connections for vessel tracking and user notifications."""

    def __init__(self):
        # Global vessel tracking subscribers
        self.vessel_subscribers: List[WebSocket] = []
        # User-specific notification subscribers: user_id -> list of WebSockets
        self.user_subscribers: Dict[int, List[WebSocket]] = {}

    async def connect_vessels(self, websocket: WebSocket):
        await websocket.accept()
        self.vessel_subscribers.append(websocket)
        logger.info(f"New vessel WS client connected. Total: {len(self.vessel_subscribers)}")

    def disconnect_vessels(self, websocket: WebSocket):
        if websocket in self.vessel_subscribers:
            self.vessel_subscribers.remove(websocket)
            logger.info("Vessel WS client disconnected.")

    async def broadcast_vessel_update(self, data: dict):
        """Broadcast live vessel AIS update to all connected clients."""
        payload = json.dumps(data)
        for connection in list(self.vessel_subscribers):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect_vessels(connection)

    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.user_subscribers:
            self.user_subscribers[user_id] = []
        self.user_subscribers[user_id].append(websocket)
        logger.info(f"User {user_id} connected to notification WS.")

    def disconnect_user(self, websocket: WebSocket, user_id: int):
        if user_id in self.user_subscribers and websocket in self.user_subscribers[user_id]:
            self.user_subscribers[user_id].remove(websocket)
            if not self.user_subscribers[user_id]:
                del self.user_subscribers[user_id]
            logger.info(f"User {user_id} disconnected from notification WS.")

    async def send_user_notification(self, user_id: int, notification_data: dict):
        """Send notification to all active devices of a specific user."""
        if user_id in self.user_subscribers:
            payload = json.dumps(notification_data)
            for connection in list(self.user_subscribers[user_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    self.disconnect_user(connection, user_id)


manager = ConnectionManager()


@router.websocket("/vessels")
async def websocket_vessels(websocket: WebSocket):
    """
    WebSocket endpoint for real-time live AIS vessel positions.
    Clients receive real-time updates as vessels report new telemetry.
    """
    await manager.connect_vessels(websocket)
    try:
        while True:
            # Keep-alive ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_vessels(websocket)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Bearer token for authentication"),
):
    """
    WebSocket endpoint for user-specific real-time notifications.
    Requires token query parameter.
    """
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect_user(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)

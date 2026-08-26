"""Notification API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


@router.get("", response_model=StandardResponse[list[NotificationResponse]])
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve notifications for the current user."""
    notifs = await NotificationService.get_user_notifications(
        db, user_id=current_user.id, unread_only=unread_only, limit=limit
    )
    return StandardResponse(data=notifs)


@router.put("/{notification_id}/read", response_model=StandardResponse[NotificationResponse])
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = await NotificationService.mark_as_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    return StandardResponse(data=notif)

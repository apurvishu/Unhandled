"""Notification service for alert dispatch and user notifications."""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.utils.errors import NotFoundException


class NotificationService:
    @classmethod
    async def create_notification(
        cls, db: AsyncSession, notif_in: NotificationCreate
    ) -> NotificationResponse:
        notif = Notification(
            user_id=notif_in.user_id,
            title=notif_in.title,
            message=notif_in.message,
            notification_type=notif_in.notification_type,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notif)
        await db.flush()
        await db.refresh(notif)
        return NotificationResponse.model_validate(notif)

    @classmethod
    async def get_user_notifications(
        cls,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[NotificationResponse]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.limit(limit)

        result = await db.execute(query)
        items = result.scalars().all()
        return [NotificationResponse.model_validate(n) for n in items]

    @classmethod
    async def mark_as_read(
        cls, db: AsyncSession, notification_id: int, user_id: int
    ) -> NotificationResponse:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if notif is None:
            raise NotFoundException("Notification", notification_id)

        notif.is_read = True
        await db.flush()
        await db.refresh(notif)
        return NotificationResponse.model_validate(notif)

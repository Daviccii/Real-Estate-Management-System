"""
Notification repository for database operations.
"""
import logging
from typing import Optional, List
from datetime import datetime
from app.utils.time import utc_now
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.notification import Notification
from app.models.user import User
from app.services.email_preference_service import notifications_opted_in
from app.services.email_service import email_service
from app.services.sms_service import send_message

logger = logging.getLogger(__name__)


def _deliver_notification_email(db: Session, notification: Notification) -> None:
    """
    Fan an in-app notification out to the recipient's inbox.

    Best-effort by design: delivery problems must never break notification
    creation, and security/transactional emails bypass this gate entirely.
    """
    try:
        user = db.get(User, notification.recipient_id)
        if user is None or not user.email:
            return
        if not notifications_opted_in(db, user.id):
            return
        email_service.send_notification_email(
            email=user.email,
            subject=notification.title,
            message=notification.message,
            user_name=user.full_name,
            title=notification.title,
        )
    except Exception:
        logger.warning(
            "Email fan-out failed for notification %s", notification.id, exc_info=True
        )


def _deliver_notification_sms(db: Session, notification: Notification) -> None:
    """
    Fan high-priority notifications out to the recipient's phone.

    SMS is reserved for HIGH/CRITICAL priority events (overdue payments,
    security alerts) to keep per-message costs bounded; ordinary in-app
    traffic never pages a phone. Best-effort like the email fan-out.
    """
    try:
        if notification.priority not in ("HIGH", "CRITICAL"):
            return
        user = db.get(User, notification.recipient_id)
        if user is None or not user.phone:
            return
        send_message(user.phone, f"PropNoxa: {notification.title} - {notification.message}")
    except Exception:
        logger.warning(
            "SMS fan-out failed for notification %s", notification.id, exc_info=True
        )


def create_notification(
    db: Session,
    *,
    recipient_id: int,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "NORMAL",
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> Notification:
    """
    Create a new notification.
    
    Args:
        db: Database session
        recipient_id: User ID of the notification recipient
        notification_type: Type of notification (PAYMENT, LEASE, MAINTENANCE, etc.)
        title: Notification title
        message: Notification message
        priority: Notification priority (LOW, NORMAL, HIGH, CRITICAL)
        related_entity_type: Type of related entity (PROPERTY, LEASE, PAYMENT, etc.)
        related_entity_id: ID of related entity
    
    Returns:
        Created Notification object
    """
    notification = Notification(
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    _deliver_notification_email(db, notification)
    _deliver_notification_sms(db, notification)
    return notification


def get_notification(db: Session, notification_id: int) -> Optional[Notification]:
    """Get a notification by ID."""
    return db.query(Notification).filter(Notification.id == notification_id).first()


def get_user_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[Notification]:
    """
    Get all notifications for a user, ordered by creation date (newest first).
    """
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == user_id)
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_unread_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[Notification]:
    """
    Get unread notifications for a user.
    """
    return (
        db.query(Notification)
        .filter(
            and_(
                Notification.recipient_id == user_id,
                Notification.is_read == False
            )
        )
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_user_unread_notifications(db: Session, user_id: int) -> int:
    """
    Count unread notifications for a user.
    """
    return (
        db.query(Notification)
        .filter(
            and_(
                Notification.recipient_id == user_id,
                Notification.is_read == False
            )
        )
        .count()
    )


def mark_notification_as_read(db: Session, notification: Notification) -> Notification:
    """
    Mark a notification as read.
    """
    notification.mark_as_read()
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_notification_as_unread(db: Session, notification: Notification) -> Notification:
    """
    Mark a notification as unread.
    """
    notification.mark_as_unread()
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_user_notifications_as_read(db: Session, user_id: int) -> int:
    """
    Mark all notifications for a user as read.
    Returns the count of notifications marked as read.
    """
    count = (
        db.query(Notification)
        .filter(
            and_(
                Notification.recipient_id == user_id,
                Notification.is_read == False
            )
        )
        .update({
            Notification.is_read: True,
            Notification.read_at: utc_now()
        })
    )
    db.commit()
    return count


def delete_notification(db: Session, notification: Notification) -> None:
    """
    Delete a notification.
    """
    db.delete(notification)
    db.commit()


def delete_user_notification(db: Session, user_id: int, notification_id: int) -> bool:
    """
    Delete a notification if it belongs to the user.
    Returns True if deleted, False if not found or unauthorized.
    """
    notification = get_notification(db, notification_id)
    if not notification or notification.recipient_id != user_id:
        return False
    
    delete_notification(db, notification)
    return True


def get_notifications_by_type(
    db: Session,
    user_id: int,
    notification_type: str,
    skip: int = 0,
    limit: int = 100,
) -> List[Notification]:
    """
    Get notifications of a specific type for a user.
    """
    return (
        db.query(Notification)
        .filter(
            and_(
                Notification.recipient_id == user_id,
                Notification.notification_type == notification_type
            )
        )
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_notifications_by_priority(
    db: Session,
    user_id: int,
    priority: str,
    skip: int = 0,
    limit: int = 100,
) -> List[Notification]:
    """
    Get notifications of a specific priority for a user.
    """
    return (
        db.query(Notification)
        .filter(
            and_(
                Notification.recipient_id == user_id,
                Notification.priority == priority
            )
        )
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

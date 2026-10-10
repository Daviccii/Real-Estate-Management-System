"""
Notification endpoints for managing user notifications.

All endpoints require authentication and enforce user isolation.
Users can only access their own notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.services.email_preference_service import get_preference, set_preference
from app.repositories.notification_repo import (
    get_notification,
    get_user_notifications,
    get_user_unread_notifications,
    count_user_unread_notifications,
    mark_notification_as_read,
    mark_notification_as_unread,
    mark_all_user_notifications_as_read,
    delete_user_notification,
    get_notifications_by_type,
    get_notifications_by_priority,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# SCHEMAS
# ============================================================================

class NotificationOut(BaseModel):
    """Notification response schema."""
    id: int
    recipient_id: int
    notification_type: str
    title: str
    message: str
    priority: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    is_read: bool
    created_at: str
    read_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationReadRequest(BaseModel):
    """Request to mark notification as read."""
    pass


class UnreadCountResponse(BaseModel):
    """Response for unread notification count."""
    unread_count: int


class EmailPreferenceOut(BaseModel):
    """Current email delivery preference. No stored row means opted in."""
    notifications_enabled: bool = True


class EmailPreferenceUpdate(BaseModel):
    """Upsert payload for the notification-email opt-out toggle."""
    notifications_enabled: bool


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/email-preferences", response_model=EmailPreferenceOut)
def read_email_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the caller's notification-email preference (default: opted in)."""
    preference = get_preference(db, current_user.id)
    return EmailPreferenceOut(
        notifications_enabled=preference.notifications_enabled if preference else True
    )


@router.put("/email-preferences", response_model=EmailPreferenceOut)
def update_email_preferences(
    payload: EmailPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Opt in or out of notification emails (security emails are never gated)."""
    preference = set_preference(db, current_user.id, notifications_enabled=payload.notifications_enabled)
    return EmailPreferenceOut(notifications_enabled=preference.notifications_enabled)


@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    skip: int = 0,
    limit: int = 100,
    notification_type: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List notifications for the current user.
    Supports filtering by type and priority.
    """
    if notification_type:
        notifications = get_notifications_by_type(
            db, current_user.id, notification_type, skip=skip, limit=limit
        )
    elif priority:
        notifications = get_notifications_by_priority(
            db, current_user.id, priority, skip=skip, limit=limit
        )
    else:
        notifications = get_user_notifications(
            db, current_user.id, skip=skip, limit=limit
        )
    
    return [
        NotificationOut(
            id=n.id,
            recipient_id=n.recipient_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            priority=n.priority,
            related_entity_type=n.related_entity_type,
            related_entity_id=n.related_entity_id,
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if n.created_at else None,
            read_at=n.read_at.isoformat() if n.read_at else None,
        )
        for n in notifications
    ]


@router.get("/unread", response_model=List[NotificationOut])
def list_unread_notifications(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List unread notifications for the current user.
    """
    notifications = get_user_unread_notifications(
        db, current_user.id, skip=skip, limit=limit
    )
    
    return [
        NotificationOut(
            id=n.id,
            recipient_id=n.recipient_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            priority=n.priority,
            related_entity_type=n.related_entity_type,
            related_entity_id=n.related_entity_id,
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if n.created_at else None,
            read_at=n.read_at.isoformat() if n.read_at else None,
        )
        for n in notifications
    ]


@router.get("/unread/count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get count of unread notifications for the current user.
    Useful for badge display in UI.
    """
    count = count_user_unread_notifications(db, current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.get("/{notification_id}", response_model=NotificationOut)
def get_single_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific notification.
    User can only access their own notifications.
    """
    notification = get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Verify user owns this notification
    if notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this notification"
        )
    
    return NotificationOut(
        id=notification.id,
        recipient_id=notification.recipient_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at.isoformat() if notification.created_at else None,
        read_at=notification.read_at.isoformat() if notification.read_at else None,
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read.
    User can only mark their own notifications.
    """
    notification = get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Verify user owns this notification
    if notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this notification"
        )
    
    notification = mark_notification_as_read(db, notification)
    
    return NotificationOut(
        id=notification.id,
        recipient_id=notification.recipient_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at.isoformat() if notification.created_at else None,
        read_at=notification.read_at.isoformat() if notification.read_at else None,
    )


@router.patch("/{notification_id}/unread", response_model=NotificationOut)
def mark_as_unread(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as unread.
    User can only mark their own notifications.
    """
    notification = get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Verify user owns this notification
    if notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this notification"
        )
    
    notification = mark_notification_as_unread(db, notification)
    
    return NotificationOut(
        id=notification.id,
        recipient_id=notification.recipient_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at.isoformat() if notification.created_at else None,
        read_at=notification.read_at.isoformat() if notification.read_at else None,
    )


@router.patch("/read-all", response_model=dict)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications for the current user as read.
    """
    count = mark_all_user_notifications_as_read(db, current_user.id)
    return {
        "message": "All notifications marked as read",
        "count": count
    }


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a notification.
    User can only delete their own notifications.
    """
    success = delete_user_notification(db, current_user.id, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or not authorized"
        )
    return None

from datetime import datetime
from app.utils.time import utc_now
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class Notification(Base):
    """
    User notification system supporting multiple notification types and priorities.
    
    Notification Types:
    - PAYMENT: Payment-related events (due, overdue, received, failed)
    - LEASE: Lease-related events (created, expiring, renewed, terminated)
    - MAINTENANCE: Maintenance requests (submitted, updated, resolved)
    - PROPERTY: Property-related events (created, updated, sold, rented)
    - INQUIRY: Property inquiries (new, responded)
    - LEAD: Sales leads (new, updated)
    - APPOINTMENT: Appointment-related events (scheduled, updated, completed)
    - SYSTEM: System-level events and announcements
    - SECURITY: Security-related events (login, role change, suspicious activity)
    - INVESTMENT: Investment-related events (returns, portfolio updates)
    - GENERAL: General/miscellaneous notifications
    
    Priority Levels:
    - LOW: Non-urgent information
    - NORMAL: Standard notifications (default)
    - HIGH: Important events requiring attention
    - CRITICAL: Urgent events requiring immediate action
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)  # PAYMENT, LEASE, MAINTENANCE, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="NORMAL", index=True)  # LOW, NORMAL, HIGH, CRITICAL
    
    # Related entity (optional)
    # Allows linking notification to specific property, lease, payment, etc.
    related_entity_type = Column(String(50), nullable=True, index=True)  # PROPERTY, LEASE, PAYMENT, etc.
    related_entity_id = Column(Integer, nullable=True, index=True)
    
    # Read status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    recipient = relationship("User", backref="notifications", foreign_keys=[recipient_id])
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = utc_now()
    
    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None

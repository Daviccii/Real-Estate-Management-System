"""
Notification service for creating notifications from various system events.

This service provides a reusable interface for creating notifications from:
- Payment events
- Lease events
- Maintenance requests
- Property events
- Inquiries/Leads
- System events
- Security events
- Investment events
- Admin events

Usage:
    from app.services.notification_service import NotificationService
    
    NotificationService.notify_payment_issue(
        db=db,
        recipient_id=manager_id,
        amount=1000.00,
        tenant_id=tenant_id
    )
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.notification_repo import create_notification


class NotificationService:
    """Reusable notification service for various system events."""
    
    # ========================================================================
    # PAYMENT NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_payment_due(
        db: Session,
        recipient_id: int,
        amount: float,
        due_date: str,
        tenant_name: str = "Tenant",
        payment_id: Optional[int] = None,
    ):
        """Notify about an upcoming payment."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="PAYMENT",
            title="Payment Due",
            message=f"Payment of ${amount:.2f} from {tenant_name} is due on {due_date}",
            priority="NORMAL",
            related_entity_type="PAYMENT",
            related_entity_id=payment_id,
        )
    
    @staticmethod
    def notify_payment_overdue(
        db: Session,
        recipient_id: int,
        amount: float,
        tenant_name: str = "Tenant",
        payment_id: Optional[int] = None,
    ):
        """Notify about an overdue payment."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="PAYMENT",
            title="⚠️ Payment Overdue",
            message=f"Payment of ${amount:.2f} from {tenant_name} is OVERDUE",
            priority="HIGH",
            related_entity_type="PAYMENT",
            related_entity_id=payment_id,
        )
    
    @staticmethod
    def notify_payment_received(
        db: Session,
        recipient_id: int,
        amount: float,
        tenant_name: str = "Tenant",
        payment_id: Optional[int] = None,
    ):
        """Notify about a payment received."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="PAYMENT",
            title="✓ Payment Received",
            message=f"Payment of ${amount:.2f} from {tenant_name} has been received",
            priority="NORMAL",
            related_entity_type="PAYMENT",
            related_entity_id=payment_id,
        )
    
    # ========================================================================
    # LEASE NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_lease_created(
        db: Session,
        recipient_id: int,
        tenant_name: str = "Tenant",
        property_name: str = "Property",
        lease_id: Optional[int] = None,
    ):
        """Notify about a new lease."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="LEASE",
            title="New Lease Created",
            message=f"New lease created for {tenant_name} at {property_name}",
            priority="NORMAL",
            related_entity_type="LEASE",
            related_entity_id=lease_id,
        )
    
    @staticmethod
    def notify_lease_expiring_soon(
        db: Session,
        recipient_id: int,
        tenant_name: str = "Tenant",
        property_name: str = "Property",
        days_until_expiration: int = 30,
        lease_id: Optional[int] = None,
    ):
        """Notify about an upcoming lease expiration."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="LEASE",
            title="⏰ Lease Expiring Soon",
            message=f"Lease for {tenant_name} at {property_name} expires in {days_until_expiration} days",
            priority="HIGH",
            related_entity_type="LEASE",
            related_entity_id=lease_id,
        )
    
    @staticmethod
    def notify_lease_terminated(
        db: Session,
        recipient_id: int,
        tenant_name: str = "Tenant",
        property_name: str = "Property",
        lease_id: Optional[int] = None,
    ):
        """Notify about lease termination."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="LEASE",
            title="Lease Terminated",
            message=f"Lease terminated for {tenant_name} at {property_name}",
            priority="NORMAL",
            related_entity_type="LEASE",
            related_entity_id=lease_id,
        )
    
    # ========================================================================
    # MAINTENANCE NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_maintenance_request_submitted(
        db: Session,
        recipient_id: int,
        title_text: str,
        property_name: str = "Property",
        maintenance_id: Optional[int] = None,
    ):
        """Notify about a new maintenance request."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="MAINTENANCE",
            title="New Maintenance Request",
            message=f"Maintenance request at {property_name}: {title_text}",
            priority="NORMAL",
            related_entity_type="MAINTENANCE",
            related_entity_id=maintenance_id,
        )
    
    @staticmethod
    def notify_maintenance_status_updated(
        db: Session,
        recipient_id: int,
        title_text: str,
        new_status: str,
        property_name: str = "Property",
        maintenance_id: Optional[int] = None,
    ):
        """Notify about maintenance status change."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="MAINTENANCE",
            title="Maintenance Status Updated",
            message=f"Maintenance at {property_name} ({title_text}) is now {new_status}",
            priority="NORMAL",
            related_entity_type="MAINTENANCE",
            related_entity_id=maintenance_id,
        )
    
    @staticmethod
    def notify_maintenance_resolved(
        db: Session,
        recipient_id: int,
        title_text: str,
        property_name: str = "Property",
        maintenance_id: Optional[int] = None,
    ):
        """Notify about resolved maintenance."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="MAINTENANCE",
            title="✓ Maintenance Resolved",
            message=f"Maintenance at {property_name} ({title_text}) has been resolved",
            priority="NORMAL",
            related_entity_type="MAINTENANCE",
            related_entity_id=maintenance_id,
        )
    
    # ========================================================================
    # PROPERTY NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_property_created(
        db: Session,
        recipient_id: int,
        property_name: str,
        location: str = "",
        property_id: Optional[int] = None,
    ):
        """Notify about a new property."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="PROPERTY",
            title="New Property Listed",
            message=f"New property: {property_name} {location}",
            priority="NORMAL",
            related_entity_type="PROPERTY",
            related_entity_id=property_id,
        )
    
    @staticmethod
    def notify_property_updated(
        db: Session,
        recipient_id: int,
        property_name: str,
        change_description: str = "",
        property_id: Optional[int] = None,
    ):
        """Notify about property update."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="PROPERTY",
            title="Property Updated",
            message=f"{property_name} has been updated. {change_description}",
            priority="NORMAL",
            related_entity_type="PROPERTY",
            related_entity_id=property_id,
        )
    
    # ========================================================================
    # INQUIRY/LEAD NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_new_inquiry(
        db: Session,
        recipient_id: int,
        property_name: str,
        inquiry_from: str = "Interested Buyer",
        inquiry_id: Optional[int] = None,
    ):
        """Notify about a new property inquiry."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="INQUIRY",
            title="New Property Inquiry",
            message=f"New inquiry for {property_name} from {inquiry_from}",
            priority="NORMAL",
            related_entity_type="INQUIRY",
            related_entity_id=inquiry_id,
        )
    
    @staticmethod
    def notify_new_lead(
        db: Session,
        recipient_id: int,
        lead_name: str,
        property_name: str = "",
        lead_id: Optional[int] = None,
    ):
        """Notify about a new lead."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="LEAD",
            title="New Lead",
            message=f"New lead from {lead_name}" + (f" for {property_name}" if property_name else ""),
            priority="NORMAL",
            related_entity_type="LEAD",
            related_entity_id=lead_id,
        )
    
    # ========================================================================
    # SYSTEM NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_system_alert(
        db: Session,
        recipient_id: int,
        title_text: str,
        message_text: str,
        priority: str = "NORMAL",
    ):
        """Notify about a system alert."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="SYSTEM",
            title=title_text,
            message=message_text,
            priority=priority,
        )
    
    # ========================================================================
    # SECURITY NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_security_event(
        db: Session,
        recipient_id: int,
        event_description: str,
        priority: str = "HIGH",
    ):
        """Notify about a security event."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="SECURITY",
            title="⚠️ Security Alert",
            message=event_description,
            priority=priority,
        )
    
    # ========================================================================
    # INVESTMENT NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_investment_update(
        db: Session,
        recipient_id: int,
        property_name: str,
        update_description: str,
        investment_id: Optional[int] = None,
    ):
        """Notify about investment portfolio update."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="INVESTMENT",
            title="Investment Update",
            message=f"Investment in {property_name}: {update_description}",
            priority="NORMAL",
            related_entity_type="INVESTMENT",
            related_entity_id=investment_id,
        )
    
    # ========================================================================
    # GENERAL NOTIFICATIONS
    # ========================================================================
    
    @staticmethod
    def notify_general(
        db: Session,
        recipient_id: int,
        title_text: str,
        message_text: str,
        priority: str = "NORMAL",
    ):
        """Create a general notification."""
        return create_notification(
            db,
            recipient_id=recipient_id,
            notification_type="GENERAL",
            title=title_text,
            message=message_text,
            priority=priority,
        )

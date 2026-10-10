import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import BackgroundJob, Notification, Property, Unit
from app.repositories.lease_repo import mark_expiring_leases
from app.utils.time import utc_now


def handle_notification_create(db: Session, payload: dict) -> dict:
    notification = Notification(**payload)
    db.add(notification)
    db.commit()
    return {"notification_id": notification.id}


def handle_lease_expiry(db: Session, payload: dict) -> dict:
    threshold = datetime.fromisoformat(payload["expiry_threshold"])
    updated = mark_expiring_leases(
        db,
        expiry_threshold=threshold,
        company_id=payload.get("company_id"),
    )
    db.commit()
    return {"updated": updated}


def handle_property_summary(db: Session, payload: dict) -> dict:
    company_id = payload["company_id"]
    properties = db.query(func.count(Property.id)).filter(Property.company_id == company_id).scalar() or 0
    units = db.query(func.count(Unit.id)).join(Property).filter(Property.company_id == company_id).scalar() or 0
    return {"company_id": company_id, "properties": properties, "units": units, "generated_at": utc_now().isoformat()}


def handle_notification_import(db: Session, payload: dict) -> dict:
    rows = payload.get("notifications", [])
    if not isinstance(rows, list):
        raise ValueError("notifications must be a list")
    db.add_all(Notification(**row) for row in rows)
    db.commit()
    return {"imported": len(rows)}


HANDLERS = {
    "notification.create": handle_notification_create,
    "lease.expiry": handle_lease_expiry,
    "report.property_summary": handle_property_summary,
    "import.notifications": handle_notification_import,
}

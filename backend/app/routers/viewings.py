from typing import List, Optional
from datetime import datetime
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import require_user, require_staff
from app.models.viewing import Viewing
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.models.notification import Notification
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/viewings", tags=["viewings"])


class ViewingCreate(BaseModel):
    property_id: int
    unit_id: Optional[int] = None
    viewing_date: Optional[str] = None  # YYYY-MM-DD
    start_time: Optional[str] = None    # HH:MM
    end_time: Optional[str] = None      # HH:MM
    scheduled_time: Optional[str] = None  # ISO timestamp fallback
    viewing_type: Optional[str] = "in_person"
    notes: Optional[str] = None


class ViewingStatusUpdate(BaseModel):
    status: str  # pending, confirmed, completed, cancelled, rescheduled
    cancellation_reason: Optional[str] = None
    feedback: Optional[str] = None


class ViewingOut(BaseModel):
    id: int
    property_id: int
    unit_id: Optional[int]
    prospect_id: int
    host_user_id: Optional[int]
    viewing_date: str
    start_time: str
    end_time: str
    status: str
    notes: Optional[str]
    cancellation_reason: Optional[str]
    feedback: Optional[str]
    created_at: datetime
    property_name: Optional[str] = None
    prospect_name: Optional[str] = None
    host_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/available-slots")
def get_available_slots(
    property_id: int,
    date: str,  # YYYY-MM-DD
    db: Session = Depends(get_db),
):
    """
    Returns available 30-minute viewing slots for a property on a given date.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if payload.unit_id is not None and not db.query(Unit).filter(
        Unit.id == payload.unit_id,
        Unit.property_id == payload.property_id,
    ).first():
        raise HTTPException(status_code=404, detail="Unit not found for this property")

    host_id = prop.agent_id or prop.manager_id or prop.owner_id
    
    # Query booked slots on this date
    booked = db.query(Viewing).filter(
        Viewing.property_id == property_id,
        Viewing.viewing_date == date,
        Viewing.status.in_(["requested", "pending", "confirmed"])
    ).all()
    
    booked_times = {v.start_time for v in booked}
    
    # Standard viewing slots (09:00 to 17:00)
    all_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
    ]
    
    available = [
        {"start_time": s, "end_time": f"{int(s[:2]) + (1 if s[3:]=='30' else 0):02d}:{'00' if s[3:]=='30' else '30'}"}
        for s in all_slots if s not in booked_times
    ]
    
    return {
        "property_id": property_id,
        "date": date,
        "host_id": host_id,
        "available_slots": available
    }


@router.post("/request", response_model=ViewingOut)
@router.post("/book", response_model=ViewingOut)
def request_viewing(
    payload: ViewingCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Prospect requests a viewing appointment.
    Prevents double booking on the same property and time.
    """
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    v_date = payload.viewing_date
    s_time = payload.start_time
    e_time = payload.end_time

    if not v_date and payload.scheduled_time:
        try:
            dt = datetime.fromisoformat(payload.scheduled_time.replace("Z", ""))
            v_date = dt.strftime("%Y-%m-%d")
            s_time = dt.strftime("%H:%M")
            e_time = (dt + timedelta(minutes=30)).strftime("%H:%M")
        except Exception:
            v_date = utc_now().strftime("%Y-%m-%d")
            s_time = "10:00"
            e_time = "10:30"
    
    if not v_date:
        v_date = utc_now().strftime("%Y-%m-%d")
    if not s_time:
        s_time = "10:00"
    if not e_time:
        e_time = "10:30"

    # Conflict check: Double booking prevention
    conflict = db.query(Viewing).filter(
        Viewing.property_id == payload.property_id,
        Viewing.viewing_date == v_date,
        Viewing.start_time == s_time,
        Viewing.status.in_(["requested", "pending", "confirmed"])
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This viewing slot is already booked. Please choose another time."
        )

    host_id = prop.agent_id or prop.manager_id or prop.owner_id

    viewing = Viewing(
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        prospect_id=current_user.id,
        host_user_id=host_id,
        viewing_date=v_date,
        start_time=s_time,
        end_time=e_time,
        notes=payload.notes,
        status="pending",
    )
    db.add(viewing)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This viewing slot was booked by another request. Please choose another time.",
        )
    db.refresh(viewing)

    # Notify host if available
    if host_id:
        notif = Notification(
            recipient_id=host_id,
            notification_type="APPOINTMENT",
            title="New Viewing Requested",
            message=f"{current_user.full_name or current_user.email} requested a viewing for '{prop.name}' on {v_date} at {s_time}.",
            priority="HIGH",
            related_entity_type="VIEWING",
            related_entity_id=viewing.id,
        )
        db.add(notif)
        db.commit()

    log_audit_event(db, current_user.id, "REQUEST_VIEWING", "viewing", viewing.id, details={"property_id": prop.id, "date": v_date})

    res = ViewingOut.model_validate(viewing, from_attributes=True)
    res.property_name = prop.name
    res.prospect_name = current_user.full_name or current_user.email
    return res


@router.get("/my", response_model=List[ViewingOut])
@router.get("/my-viewings", response_model=List[ViewingOut])
def get_my_viewings(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Returns all viewings requested by or hosted by the current user.
    """
    viewings = db.query(Viewing).filter(
        (Viewing.prospect_id == current_user.id) | (Viewing.host_user_id == current_user.id)
    ).order_by(Viewing.created_at.desc()).all()

    out = []
    for v in viewings:
        item = ViewingOut.model_validate(v, from_attributes=True)
        if v.property:
            item.property_name = v.property.name
        if v.prospect:
            item.prospect_name = v.prospect.full_name or v.prospect.email
        if v.host_user:
            item.host_name = v.host_user.full_name or v.host_user.email
        out.append(item)
    return out


@router.put("/{viewing_id}/status", response_model=ViewingOut)
def update_viewing_status(
    viewing_id: int,
    payload: ViewingStatusUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Update status of a viewing (confirm, complete, cancel).
    Enforces authorization: Only host, prospect, or admin can modify status.
    """
    viewing = db.query(Viewing).filter(Viewing.id == viewing_id).first()
    if not viewing:
        raise HTTPException(status_code=404, detail="Viewing not found")

    is_host = viewing.host_user_id == current_user.id
    is_prospect = viewing.prospect_id == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_host or is_prospect or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to update this viewing")

    viewing.status = payload.status
    if payload.cancellation_reason:
        viewing.cancellation_reason = payload.cancellation_reason
    if payload.feedback:
        viewing.feedback = payload.feedback

    db.commit()
    db.refresh(viewing)

    # Notify counterpart
    target_recipient_id = viewing.prospect_id if is_host else viewing.host_user_id
    if target_recipient_id:
        notif = Notification(
            recipient_id=target_recipient_id,
            notification_type="APPOINTMENT",
            title=f"Viewing Appointment {payload.status.capitalize()}",
            message=f"Viewing on {viewing.viewing_date} at {viewing.start_time} has been updated to '{payload.status}'.",
            priority="NORMAL",
            related_entity_type="VIEWING",
            related_entity_id=viewing.id,
        )
        db.add(notif)
        db.commit()

    log_audit_event(db, current_user.id, f"UPDATE_VIEWING_{payload.status.upper()}", "viewing", viewing.id)

    res = ViewingOut.model_validate(viewing, from_attributes=True)
    if viewing.property:
        res.property_name = viewing.property.name
    return res

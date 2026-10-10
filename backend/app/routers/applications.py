from typing import List, Optional
from datetime import datetime, timedelta
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_user, require_management, require_admin
from app.models.application import RentalApplication, ApplicationReviewHistory
from app.models.property import Property
from app.models.unit import Unit
from app.models.user import User
from app.models.lease import Lease
from app.models.notification import Notification
from app.services.audit_service import log_audit_event
from app.config.settings import settings

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    property_id: int
    unit_id: Optional[int] = None
    desired_move_in_date: Optional[str] = None
    monthly_income: Optional[str] = None
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    credit_score_range: Optional[str] = None
    occupants_count: Optional[int] = 1
    has_pets: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    references_json: Optional[str] = None
    documents_json: Optional[str] = None
    notes: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: str  # under_review, info_required, approved, rejected, withdrawn
    review_notes: Optional[str] = None


class ConvertToLeasePayload(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    rent_amount: str
    deposit: Optional[str] = None
    payment_due_date: Optional[int] = 1
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    applicant_id: int
    property_id: int
    unit_id: Optional[int]
    status: str
    desired_move_in_date: Optional[datetime]
    monthly_income: Optional[str]
    employment_status: Optional[str]
    employer_name: Optional[str]
    job_title: Optional[str]
    credit_score_range: Optional[str]
    occupants_count: Optional[int]
    has_pets: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    references_json: Optional[str]
    documents_json: Optional[str]
    reviewed_by_id: Optional[int]
    review_notes: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    property_name: Optional[str] = None
    unit_number: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=ApplicationOut)
@router.post("/apply", response_model=ApplicationOut)
def submit_application(
    payload: ApplicationCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Prospective tenant submits a rental application for a property/unit.
    """
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if payload.unit_id is not None:
        unit = db.query(Unit).filter(
            Unit.id == payload.unit_id,
            Unit.property_id == payload.property_id,
        ).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found for this property")

    move_in = None
    if payload.desired_move_in_date:
        try:
            move_in = datetime.fromisoformat(payload.desired_move_in_date.replace("Z", ""))
        except Exception:
            pass

    app_record = RentalApplication(
        applicant_id=current_user.id,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        status="submitted",
        desired_move_in_date=move_in,
        monthly_income=payload.monthly_income,
        employment_status=payload.employment_status,
        employer_name=payload.employer_name,
        job_title=payload.job_title,
        credit_score_range=payload.credit_score_range,
        occupants_count=payload.occupants_count or 1,
        has_pets=payload.has_pets,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
        references_json=payload.references_json,
        documents_json=payload.documents_json,
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    # Add initial history
    history = ApplicationReviewHistory(
        application_id=app_record.id,
        previous_status=None,
        new_status="submitted",
        changed_by_id=current_user.id,
        notes="Application submitted by applicant."
    )
    db.add(history)

    # Notify Landlord/Manager
    reviewers = [prop.owner_id, prop.manager_id]
    for r_id in filter(None, set(reviewers)):
        notif = Notification(
            recipient_id=r_id,
            notification_type="APPLICATION",
            title="New Rental Application",
            message=f"{current_user.full_name or current_user.email} submitted an application for '{prop.name}'.",
            priority="HIGH",
            related_entity_type="APPLICATION",
            related_entity_id=app_record.id,
        )
        db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "SUBMIT_RENTAL_APPLICATION", "rental_application", app_record.id, details={"property_id": prop.id})

    res = ApplicationOut.model_validate(app_record, from_attributes=True)
    res.property_name = prop.name
    res.applicant_name = current_user.full_name or current_user.email
    return res


@router.get("/my", response_model=List[ApplicationOut])
def get_my_applications(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
):
    """
    Tenant retrieves their own submitted applications.
    """
    apps = db.query(RentalApplication).filter(
        RentalApplication.applicant_id == current_user.id
    ).order_by(RentalApplication.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    out = []
    for a in apps:
        item = ApplicationOut.model_validate(a, from_attributes=True)
        if a.property:
            item.property_name = a.property.name
        if a.unit:
            item.unit_number = a.unit.unit_number
        item.applicant_name = current_user.full_name or current_user.email
        item.applicant_email = current_user.email
        out.append(item)
    return out


@router.get("/property/{property_id}", response_model=List[ApplicationOut])
def get_property_applications(
    property_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
):
    """
    Landlord, Manager, or Admin retrieves all applications for a property they manage/own.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.company_id is not None and prop.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Property not found")

    is_owner = prop.owner_id == current_user.id
    is_manager = prop.manager_id == current_user.id
    is_agent = prop.agent_id == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_owner or is_manager or is_agent or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to review applications for this property")

    apps = db.query(RentalApplication).filter(
        RentalApplication.property_id == property_id
    ).order_by(RentalApplication.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    out = []
    for a in apps:
        item = ApplicationOut.model_validate(a, from_attributes=True)
        item.property_name = prop.name
        if a.unit:
            item.unit_number = a.unit.unit_number
        if a.applicant:
            item.applicant_name = a.applicant.full_name or a.applicant.email
            item.applicant_email = a.applicant.email
        out.append(item)
    return out


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application_details(
    application_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Get full details for an application.
    Enforces authorization: Applicant, Owner, Manager, Agent, or Admin.
    """
    app_record = db.query(RentalApplication).filter(RentalApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    prop = app_record.property
    if not prop or not company_resource_access(current_user, prop):
        raise HTTPException(status_code=404, detail="Application not found")
    is_applicant = app_record.applicant_id == current_user.id
    is_owner = prop and prop.owner_id == current_user.id
    is_manager = prop and prop.manager_id == current_user.id
    is_agent = prop and prop.agent_id == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_applicant or is_owner or is_manager or is_agent or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to view this application")

    item = ApplicationOut.model_validate(app_record, from_attributes=True)
    if prop:
        item.property_name = prop.name
    if app_record.unit:
        item.unit_number = app_record.unit.unit_number
    if app_record.applicant:
        item.applicant_name = app_record.applicant.full_name or app_record.applicant.email
        item.applicant_email = app_record.applicant.email
    return item


@router.put("/{application_id}/status", response_model=ApplicationOut)
@router.patch("/{application_id}/status", response_model=ApplicationOut)
@router.patch("/{application_id}/review", response_model=ApplicationOut)
@router.put("/{application_id}/review", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Update application status (approve, reject, request additional info, etc.).
    """
    app_record = db.query(RentalApplication).filter(RentalApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    prop = app_record.property
    is_applicant = app_record.applicant_id == current_user.id
    is_management = prop and (prop.owner_id == current_user.id or prop.manager_id == current_user.id)
    is_admin = current_user.role == "admin"

    # Applicants can only withdraw their own application
    if is_applicant and payload.status != "withdrawn" and not (is_management or is_admin):
        raise HTTPException(status_code=403, detail="Applicants can only withdraw their application")

    if not (is_applicant or is_management or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to review this application")

    old_status = app_record.status
    app_record.status = payload.status
    app_record.reviewed_by_id = current_user.id
    app_record.review_notes = payload.review_notes
    app_record.reviewed_at = utc_now()

    history = ApplicationReviewHistory(
        application_id=app_record.id,
        previous_status=old_status,
        new_status=payload.status,
        changed_by_id=current_user.id,
        notes=payload.review_notes
    )
    db.add(history)
    db.commit()
    db.refresh(app_record)

    # Notify applicant
    notif = Notification(
        recipient_id=app_record.applicant_id,
        notification_type="APPLICATION",
        title=f"Application {payload.status.replace('_', ' ').capitalize()}",
        message=f"Your application for '{prop.name if prop else 'property'}' is now '{payload.status}'. Notes: {payload.review_notes or 'None'}",
        priority="HIGH" if payload.status == "approved" else "NORMAL",
        related_entity_type="APPLICATION",
        related_entity_id=app_record.id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, f"APPLICATION_{payload.status.upper()}", "rental_application", app_record.id)

    item = ApplicationOut.model_validate(app_record, from_attributes=True)
    if prop:
        item.property_name = prop.name
    return item


@router.post("/{application_id}/convert-to-lease")
def convert_application_to_lease(
    application_id: int,
    payload: ConvertToLeasePayload,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Converts an APPROVED application directly into an active/draft Lease.
    Links the tenant, unit, and property seamlessly without re-typing.
    """
    app_record = db.query(RentalApplication).filter(RentalApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    prop = app_record.property
    is_management = prop and (prop.owner_id == current_user.id or prop.manager_id == current_user.id)
    is_admin = current_user.role == "admin"

    if not (is_management or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to create a lease for this application")

    if app_record.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved applications can be converted to a lease")

    start_dt = datetime.fromisoformat(payload.start_date.replace("Z", ""))
    end_dt = datetime.fromisoformat(payload.end_date.replace("Z", ""))

    # Auto-find unit if unit_id is missing
    target_unit_id = app_record.unit_id
    if not target_unit_id:
        unit = db.query(Unit).filter(Unit.property_id == app_record.property_id).first()
        if unit:
            target_unit_id = unit.id

    if not target_unit_id:
        raise HTTPException(status_code=400, detail="A valid unit is required to generate a lease")
    unit_obj = db.query(Unit).filter(
        Unit.id == target_unit_id,
        Unit.property_id == app_record.property_id,
    ).first()
    if not unit_obj:
        raise HTTPException(status_code=400, detail="A valid unit is required to generate a lease")

    lease = Lease(
        tenant_id=app_record.applicant_id,
        unit_id=target_unit_id,
        property_id=app_record.property_id,
        start_date=start_dt,
        end_date=end_dt,
        rent_amount=payload.rent_amount,
        deposit=payload.deposit or "0",
        payment_due_date=payload.payment_due_date or 1,
        status="active",
        notes=payload.notes or f"Created from approved Application #{app_record.id}"
    )
    db.add(lease)

    # Ensure applicant role is updated to tenant if previously user
    applicant = db.query(User).filter(User.id == app_record.applicant_id).first()
    if applicant and applicant.role == "user":
        applicant.role = "tenant"

    # Mark unit occupied
    unit_obj.status = "occupied"

    db.commit()
    db.refresh(lease)

    # Notify new tenant
    notif = Notification(
        recipient_id=app_record.applicant_id,
        notification_type="LEASE",
        title="Lease Agreement Activated!",
        message=f"Welcome! Your lease for '{prop.name}' has been created. Start Date: {payload.start_date}.",
        priority="CRITICAL",
        related_entity_type="LEASE",
        related_entity_id=lease.id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "CONVERT_APPLICATION_TO_LEASE", "lease", lease.id, details={"application_id": app_record.id})

    return {
        "message": "Lease created successfully from application",
        "lease_id": lease.id,
        "tenant_id": lease.tenant_id,
        "property_id": lease.property_id,
        "status": lease.status
    }

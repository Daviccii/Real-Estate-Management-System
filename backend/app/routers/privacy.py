"""
Privacy / GDPR endpoints.

- GET  /privacy/export                        Authenticated JSON export download
- POST /privacy/consent                       Consent recording (anonymous or authenticated)
- GET  /privacy/delete-request                Status of the caller's latest request
- POST /privacy/delete-request                Request account deletion
- DELETE /privacy/delete-request              Cancel a pending request
- GET  /privacy/admin/deletion-requests       Admin queue
- POST /privacy/admin/deletion-requests/{id}/execute  Admin executes erasure
- POST /privacy/admin/deletion-requests/{id}/decline  Admin declines with reason
"""
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_optional_user
from app.auth.roles import require_admin
from app.database.database import get_db
from app.models import DataDeletionRequest, User
from app.services import privacy_service

router = APIRouter(prefix="/privacy", tags=["privacy"])

VALID_CONSENT_TYPES = {"cookie_analytics", "cookie_marketing", "tos"}


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool
    policy_version: str = "1.0"
    client_id: Optional[str] = None

    @field_validator("consent_type")
    @classmethod
    def validate_consent_type(cls, v: str) -> str:
        if v not in VALID_CONSENT_TYPES:
            raise ValueError(f"consent_type must be one of {sorted(VALID_CONSENT_TYPES)}")
        return v

    @field_validator("client_id", "policy_version")
    @classmethod
    def strip_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class DeletionRequestPayload(BaseModel):
    reason: Optional[str] = None


class DeclinePayload(BaseModel):
    notes: Optional[str] = None


def _request_payload(request_obj: DataDeletionRequest) -> dict:
    return {
        "id": request_obj.id,
        "user_id": request_obj.user_id,
        "status": request_obj.status,
        "reason": request_obj.reason,
        "requested_at": request_obj.requested_at.isoformat() if request_obj.requested_at else None,
        "processed_at": request_obj.processed_at.isoformat() if request_obj.processed_at else None,
        "notes": request_obj.notes,
    }


@router.get("/export")
def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = privacy_service.export_user_data(db, current_user)
    filename = f"propnoxa-data-export-user-{current_user.id}.json"
    return Response(
        content=json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/consent")
async def record_consent(
    payload: ConsentRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    record = privacy_service.record_consent(
        db,
        consent_type=payload.consent_type,
        granted=payload.granted,
        user=current_user,
        client_id=payload.client_id,
        policy_version=payload.policy_version,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"id": record.id, "recorded": True}


@router.get("/delete-request")
def get_deletion_request(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(DataDeletionRequest)
        .filter(DataDeletionRequest.user_id == current_user.id)
        .order_by(DataDeletionRequest.id.desc())
        .first()
    )
    if not latest:
        return {"request": None}
    return {"request": _request_payload(latest)}


@router.post("/delete-request", status_code=status.HTTP_202_ACCEPTED)
def create_deletion_request(
    payload: DeletionRequestPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request_obj, created = privacy_service.request_account_deletion(db, current_user, payload.reason)
    return {
        "request": _request_payload(request_obj),
        "created": created,
        "message": "Deletion request already pending" if not created else "Deletion request received",
    }


@router.delete("/delete-request")
def cancel_deletion_request(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not privacy_service.cancel_account_deletion(db, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending deletion request")
    return {"message": "Deletion request cancelled"}


@router.get("/admin/deletion-requests")
def list_deletion_requests(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DataDeletionRequest)
        .order_by(DataDeletionRequest.status.desc(), DataDeletionRequest.requested_at.desc())
        .all()
    )
    return {"requests": [_request_payload(r) for r in rows]}


@router.post("/admin/deletion-requests/{request_id}/execute")
def execute_deletion_request(
    request_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    request_obj = db.query(DataDeletionRequest).filter(DataDeletionRequest.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if request_obj.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is {request_obj.status}, not pending")

    result = privacy_service.execute_account_deletion(db, request_obj, admin_user)
    return result


@router.post("/admin/deletion-requests/{request_id}/decline")
def decline_deletion_request(
    request_id: int,
    payload: DeclinePayload,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    request_obj = db.query(DataDeletionRequest).filter(DataDeletionRequest.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if request_obj.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is {request_obj.status}, not pending")

    updated = privacy_service.decline_account_deletion(db, request_obj, admin_user, payload.notes)
    return {"request": _request_payload(updated)}

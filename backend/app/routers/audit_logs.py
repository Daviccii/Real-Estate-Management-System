from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.auth.roles import require_admin
from app.models.audit_log import AuditLog
from app.services.audit_chain import verify_audit_chain

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"], dependencies=[Depends(require_admin)])


class AuditLogOut(BaseModel):
    id: int
    actor_id: Optional[int]
    actor_name: Optional[str] = None
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    ip_address: Optional[str]
    details_json: Optional[str]
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditChainVerificationOut(BaseModel):
    verified: bool
    entries_checked: int
    root: Optional[Dict[str, Any]] = None
    first_entry_id: Optional[int] = None
    last_entry_id: Optional[int] = None
    tip_hash: Optional[str] = None
    first_broken: Optional[Dict[str, Any]] = None
    checked_at: datetime


@router.get("/", response_model=List[AuditLogOut])
def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Search and filter immutable audit log entries (Administrator only).
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    out = []
    for l in logs:
        item = AuditLogOut.model_validate(l, from_attributes=True)
        if l.actor:
            item.actor_name = l.actor.full_name or l.actor.email
        out.append(item)
    return out


@router.get("/chain/verify", response_model=AuditChainVerificationOut)
def verify_chain(db: Session = Depends(get_db)):
    """
    Recompute the tamper-evident hash chain over every audit entry and report
    the first deviation (if any): edited row, deleted row, reordered row, or
    entry written outside the chained insert path. Retention-declared prunes
    (AUDIT_CHAIN_ANCHOR entries) are accepted. Administrator only.
    """
    return verify_audit_chain(db)

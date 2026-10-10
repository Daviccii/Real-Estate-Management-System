"""Reporting & export endpoints (P4-39).

`GET /reports/{report_type}` returns a JSON preview or a CSV attachment,
scoped to the caller's properties (admin: all, owner: owned, manager:
assigned). Downloads are audited as security events because exported
files leave the system's access-control boundary.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.roles import require_role
from app.database.database import get_db
from app.models.user import User
from app.services.reports_service import (
    REPORT_TYPES,
    as_naive_utc,
    build_report,
    scope_property_ids,
    to_csv,
)
from app.services.security_events import emit_security_event
from app.utils.time import utc_now

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_type}")
def get_report(
    report_type: str,
    request: Request,
    date_from: Optional[datetime] = Query(None, description="Inclusive lower bound (ISO date/time)"),
    date_to: Optional[datetime] = Query(None, description="Inclusive upper bound (ISO date/time)"),
    property_id: Optional[int] = Query(None, ge=1),
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(require_role(["manager", "owner", "admin"])),
    db: Session = Depends(get_db),
):
    if report_type not in REPORT_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown report type. Supported: {', '.join(REPORT_TYPES)}",
        )
    if date_from and date_to and as_naive_utc(date_from) > as_naive_utc(date_to):
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")

    scope = scope_property_ids(db, current_user)
    if property_id is not None and scope is not None and property_id not in scope:
        # Same response as a missing property so out-of-scope ids leak nothing.
        raise HTTPException(status_code=404, detail="Property not found")

    report = build_report(
        db,
        report_type,
        property_ids=scope,
        date_from=date_from,
        date_to=date_to,
        property_id=property_id,
    )

    emit_security_event(
        "report.exported",
        request=request,
        user_id=current_user.id,
        actor=current_user.email,
        outcome="success",
        severity="info",
        details={
            "report_type": report_type,
            "format": format,
            "rows": len(report["rows"]),
            "property_id": property_id,
        },
    )

    if format == "csv":
        filename = f"propnoxa_{report_type}_report_{utc_now():%Y%m%d}.csv"
        return Response(
            content=to_csv(report),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return report

"""Analytics dashboard endpoint (P4-34).

`GET /analytics/dashboard` returns a single role-scoped payload (admin: all
properties, owner: owned, manager: assigned) consumed by the portal analytics
pages: KPIs, zero-filled month series and distributions. Dashboard loads are
not audited as security events — they are routine page views, unlike report
exports which leave the system's access-control boundary.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.roles import require_role
from app.database.database import get_db
from app.models.user import User
from app.services.analytics_service import (
    DEFAULT_MONTHS,
    MONTHS_MAX,
    MONTHS_MIN,
    build_analytics,
)
from app.services.reports_service import scope_property_ids

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_analytics_dashboard(
    months: int = Query(DEFAULT_MONTHS, ge=MONTHS_MIN, le=MONTHS_MAX),
    current_user: User = Depends(require_role(["manager", "owner", "admin"])),
    db: Session = Depends(get_db),
):
    return build_analytics(
        db,
        property_ids=scope_property_ids(db, current_user),
        months=months,
    )

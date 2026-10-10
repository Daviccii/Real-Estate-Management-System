import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
import logging

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    actor_id: Optional[int],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Any] = None,
) -> Optional[AuditLog]:
    """
    Append an event to the immutable AuditLog table.
    """
    try:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=details_str,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        logger.error(f"Failed to write audit log event: {e}")
        db.rollback()
        return None

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    insert,
    select,
    update,
)
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.audit_chain_state import AuditChainState
from app.utils.audit_hash import (
    GENESIS_PREV,
    compute_entry_hash,
    entry_payload,
    normalize_created_at,
)
from app.utils.time import utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE_PROPERTY, UPDATE_LEASE, etc.
    entity_type = Column(String(50), nullable=True, index=True)  # property, lease, user, payment, application
    entity_id = Column(Integer, nullable=True, index=True)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=True)

    # Tamper-evident chain: prev_hash links to the previous entry's
    # entry_hash; entry_hash = HMAC(key, prev_hash + canonical payload).
    # Both are written by the hook below on every insert. NULL only on rows
    # that predate the chain and somehow bypassed the backfill migration.
    prev_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True)

    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)

    actor = relationship("User", foreign_keys=[actor_id])


@event.listens_for(AuditLog, "before_insert")
def _chain_audit_entry(mapper, connection, target):
    """Stamp prev_hash/entry_hash on every audit entry, whatever wrote it."""
    if target.created_at is None:
        target.created_at = utc_now()
    # Hash the storage form (naive UTC) so that verification, which reads the
    # value back from the database, recomputes an identical payload.
    target.created_at = normalize_created_at(target.created_at)

    tip_stmt = select(AuditChainState.last_entry_hash).where(AuditChainState.id == 1)
    if connection.dialect.name == "postgresql":
        # Blocks concurrent writers on the tip row until we commit, so two
        # transactions cannot chain onto the same predecessor.
        tip_stmt = tip_stmt.with_for_update()
    tip_row = connection.execute(tip_stmt).first()
    prev = (tip_row[0] if tip_row else None) or GENESIS_PREV

    target.prev_hash = prev
    target.entry_hash = compute_entry_hash(prev, entry_payload(target))

    # Statements issued on the connection run immediately (unlike the
    # deferred ORM INSERT), so entries flushed together still chain onto each
    # other, and a rolled-back transaction rolls the tip back with it.
    if tip_row is None:
        connection.execute(
            insert(AuditChainState).values(id=1, last_entry_hash=target.entry_hash)
        )
    else:
        connection.execute(
            update(AuditChainState)
            .where(AuditChainState.id == 1)
            .values(last_entry_hash=target.entry_hash)
        )

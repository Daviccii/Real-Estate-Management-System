from sqlalchemy import Column, Integer, String

from app.models.base import Base


class AuditChainState(Base):
    """Single-row chain head for the tamper-evident audit log.

    A dedicated tip row (rather than "read the newest audit row") is what
    lets several entries added in one flush chain correctly: each BEFORE
    INSERT hook advances this row immediately, so the next entry in the same
    batch sees it, and SELECT ... FOR UPDATE serializes concurrent writers.
    ``last_entry_hash`` is NULL when the chain is empty (fresh database, or
    retention pruned everything), meaning the next entry links to GENESIS.
    """

    __tablename__ = "audit_chain_state"

    id = Column(Integer, primary_key=True)
    last_entry_hash = Column(String(64), nullable=True)

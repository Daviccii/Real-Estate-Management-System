from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
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
    
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

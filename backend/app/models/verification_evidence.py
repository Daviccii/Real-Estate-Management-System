from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class VerificationEvidence(Base):
    __tablename__ = "verification_evidence"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verification_records.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False)
    reference = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    verification = relationship("VerificationRecord", back_populates="evidence")
    created_by = relationship("User", foreign_keys=[created_by_id])

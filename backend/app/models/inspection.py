from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id = Column(Integer, primary_key=True, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # inspection_type: move_in, move_out, routine
    inspection_type = Column(String(50), nullable=False, default="move_in", index=True)
    inspector_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Structured checklist JSON and condition notes
    condition_checklist_json = Column(Text, nullable=True)
    photo_urls_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    overall_condition = Column(String(50), nullable=True, default="good")  # excellent, good, fair, poor
    
    tenant_signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    lease = relationship("Lease", backref="inspections")
    property = relationship("Property", backref="inspections")
    unit = relationship("Unit", backref="inspections")
    inspector = relationship("User", foreign_keys=[inspector_id])

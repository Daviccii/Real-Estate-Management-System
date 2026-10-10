from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class RentalApplication(Base):
    __tablename__ = "rental_applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status: draft, submitted, under_review, info_required, approved, rejected, withdrawn
    status = Column(String(50), nullable=False, default="submitted", index=True)
    desired_move_in_date = Column(DateTime, nullable=True)
    
    # Employment & Financial Information
    monthly_income = Column(String(100), nullable=True)
    employment_status = Column(String(100), nullable=True)  # employed, self-employed, student, retired
    employer_name = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    credit_score_range = Column(String(50), nullable=True)
    
    # Personal & Background Info
    occupants_count = Column(Integer, nullable=True, default=1)
    has_pets = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(100), nullable=True)
    references_json = Column(Text, nullable=True)  # JSON string of references
    documents_json = Column(Text, nullable=True)  # JSON string of uploaded doc URLs (ID, payslip)
    
    # Reviewer Information
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    applicant = relationship("User", foreign_keys=[applicant_id], backref="rental_applications")
    property = relationship("Property", foreign_keys=[property_id], backref="rental_applications")
    unit = relationship("Unit", foreign_keys=[unit_id], backref="rental_applications")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])


class ApplicationReviewHistory(Base):
    __tablename__ = "application_review_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("rental_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    application = relationship("RentalApplication", backref="status_history")
    changed_by = relationship("User", foreign_keys=[changed_by_id])

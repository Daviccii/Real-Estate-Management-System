from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship, backref

from app.models.base import Base
from app.utils.time import utc_now


class ServiceProviderProfile(Base):
    __tablename__ = "service_provider_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_name = Column(String(255), nullable=False)
    specialty = Column(String(100), nullable=False)  # plumbing, electrical, hvac, carpentry, painting, general
    license_number = Column(String(100), nullable=True)
    hourly_rate = Column(String(50), nullable=True)
    years_experience = Column(Integer, nullable=True, default=1)
    is_verified = Column(Boolean, nullable=False, default=False)
    rating = Column(Float, nullable=True, default=5.0)
    reviews_count = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    bio = Column(Text, nullable=True)
    service_areas = Column(String(255), nullable=True)  # Cities or counties served
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("service_provider_profile", cascade="all, delete-orphan", passive_deletes=True), passive_deletes=True)


class MaintenanceQuote(Base):
    __tablename__ = "maintenance_quotes"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    estimated_hours = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, accepted, rejected
    
    created_at = Column(DateTime, nullable=False, default=utc_now)

    maintenance = relationship("Maintenance", backref="quotes")
    provider = relationship("User", foreign_keys=[provider_id])


class MaintenanceWorkOrder(Base):
    __tablename__ = "maintenance_work_orders"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quote_id = Column(Integer, ForeignKey("maintenance_quotes.id", ondelete="SET NULL"), nullable=True)
    
    # Status: assigned, accepted, in_progress, completed, verified
    status = Column(String(50), nullable=False, default="assigned", index=True)
    scheduled_date = Column(DateTime, nullable=True)
    completion_notes = Column(Text, nullable=True)
    completion_photos_json = Column(Text, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    maintenance = relationship("Maintenance", backref="work_orders")
    provider = relationship("User", foreign_keys=[provider_id])
    quote = relationship("MaintenanceQuote", foreign_keys=[quote_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])

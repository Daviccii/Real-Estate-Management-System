from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship, backref

from app.models.base import Base
from app.utils.time import utc_now


class TenantProfile(Base):
    __tablename__ = "tenant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    preferred_locations = Column(String(255), nullable=True)  # e.g. "Nairobi, Westlands, Kilimani"
    min_budget = Column(Float, nullable=True)
    max_budget = Column(Float, nullable=True)
    preferred_bedrooms = Column(Integer, nullable=True)
    preferred_property_type = Column(String(50), nullable=True)  # apartment, house, townhouse
    desired_move_in_date = Column(String(50), nullable=True)
    household_size = Column(Integer, nullable=True, default=1)
    has_pets = Column(String(50), nullable=True, default="no")
    employment_status = Column(String(50), nullable=True)  # employed, self_employed, contractor, student
    monthly_income = Column(String(50), nullable=True)
    employer_name = Column(String(255), nullable=True)
    job_title = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("tenant_profile", cascade="all, delete-orphan", passive_deletes=True), passive_deletes=True)


class OwnerProfile(Base):
    __tablename__ = "owner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    owner_type = Column(String(50), nullable=False, default="individual")  # individual, company, trust, family
    company_name = Column(String(255), nullable=True)
    tax_pin = Column(String(100), nullable=True)  # KRA PIN or corporate tax ID
    national_id_number = Column(String(100), nullable=True)
    payout_phone = Column(String(50), nullable=True)  # M-Pesa or wire payout
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(100), nullable=True)
    bank_account_name = Column(String(255), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("owner_profile", cascade="all, delete-orphan", passive_deletes=True), passive_deletes=True)


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    agency_name = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)  # EARB Registration
    operating_areas = Column(String(255), nullable=True)  # e.g. "Westlands, Karen, Riverside"
    specialties = Column(String(255), nullable=True)  # Residential Luxury, Commercial, Rentals
    years_experience = Column(Integer, nullable=True, default=1)
    bio = Column(Text, nullable=True)
    commission_rate = Column(Float, nullable=True, default=5.0)  # Standard commission %
    is_verified = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("agent_profile", cascade="all, delete-orphan", passive_deletes=True), passive_deletes=True)


class ManagerProfile(Base):
    __tablename__ = "manager_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    company_name = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    operating_areas = Column(String(255), nullable=True)
    max_managed_units = Column(Integer, nullable=True, default=50)
    emergency_phone = Column(String(50), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=True)  # Provisioned by admin
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("manager_profile", cascade="all, delete-orphan", passive_deletes=True), passive_deletes=True)

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    users = relationship("User", back_populates="company")
    properties = relationship("Property", back_populates="company")


class CompanyInvitation(Base):
    __tablename__ = "company_invitations"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    email = Column(String(320), nullable=False)
    role = Column(String(50), nullable=False)
    token_hash = Column(String(128), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    company = relationship("Company")
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    __table_args__ = (
        Index("ix_company_invitations_lookup", "company_id", "email", "accepted_at"),
    )

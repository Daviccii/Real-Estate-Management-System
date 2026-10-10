from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, synonym

from app.models.base import Base
from app.utils.time import utc_now


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_number = Column(String(50), nullable=False, index=True)
    unit_type = Column(String(100), nullable=True, index=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    area = Column(String(100), nullable=True)
    rent = Column(String(100), nullable=True)
    # Backwards-compatible name used by older integrations and fixtures.
    rent_amount = synonym("rent")
    status = Column(String(50), nullable=False, default="available", index=True)
    availability_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    property = relationship("Property", backref="units")
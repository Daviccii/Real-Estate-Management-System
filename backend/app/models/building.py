from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    building_type = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(200), nullable=True, index=True)
    county = Column(String(200), nullable=True, index=True)
    sub_location = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    landmark = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    total_floors = Column(Integer, nullable=True, default=1)
    units_count = Column(Integer, nullable=True, default=0)
    amenities = Column(Text, nullable=True)  # JSON or comma-separated list of amenities
    year_built = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    property = relationship("Property", foreign_keys=[property_id], backref="buildings_list")


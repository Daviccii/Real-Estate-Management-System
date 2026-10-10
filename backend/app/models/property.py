from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    property_type = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(200), nullable=True, index=True)
    county = Column(String(200), nullable=True, index=True)
    sub_location = Column(String(200), nullable=True)
    country = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    units_count = Column(Integer, nullable=True, default=1)
    price = Column(String(100), nullable=True)
    price_label = Column(String(100), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    area = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
    gallery_urls = Column(Text, nullable=True)  # JSON array or newline-separated image URLs
    showroom_url = Column(String(500), nullable=True)
    construction_status = Column(String(50), nullable=True, default="completed")
    completion_date = Column(DateTime, nullable=True)
    planned_finish_description = Column(Text, nullable=True)
    planned_finish_image_url = Column(String(500), nullable=True)
    purpose = Column(String(50), nullable=True, index=True)
    deposit = Column(String(100), nullable=True)
    lease_term = Column(String(100), nullable=True)
    availability_date = Column(DateTime, nullable=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="SET NULL", use_alter=True, name="fk_property_building"), nullable=True, index=True)
    amenities = Column(Text, nullable=True)  # JSON or comma-separated list of amenities
    furnishing = Column(String(50), nullable=True)  # unfurnished, semi-furnished, fully-furnished
    parking_spaces = Column(Integer, nullable=True, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    landmark = Column(String(255), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, index=True)
    # Owner consent: when True, the property's direct contact details may be
    # revealed to signed-in prospects (Kenya Data Protection Act, 2019).
    allow_direct_contact = Column(Boolean, nullable=False, default=False)
    source_id = Column(Integer, ForeignKey("property_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(50), nullable=False, default="PROP_NOXA_VERIFIED")
    source_name = Column(String(255), nullable=True)
    source_reference = Column(String(255), nullable=True)
    verification_status = Column(String(50), nullable=False, default="PENDING_VERIFICATION", index=True)
    last_verified_at = Column(DateTime, nullable=True)
    listing_status = Column(String(50), nullable=False, default="ACTIVE", index=True)
    is_demo = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owner = relationship("User", foreign_keys=[owner_id])
    company = relationship("Company", back_populates="properties")
    manager = relationship("User", foreign_keys=[manager_id])
    agent = relationship("User", foreign_keys=[agent_id])
    building = relationship("Building", foreign_keys=[building_id], overlaps="buildings_list,property")
    source = relationship("PropertySource", back_populates="properties")
    media = relationship(
        "PropertyMedia",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="noload",
    )

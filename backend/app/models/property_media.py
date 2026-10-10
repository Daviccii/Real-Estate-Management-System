from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class PropertyMedia(Base):
    __tablename__ = "property_media"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    media_type = Column(String(30), nullable=False, default="image")
    source_type = Column(String(50), nullable=False, default="OWNER_UPLOADED")
    source_name = Column(String(255), nullable=True)
    license_reference = Column(String(500), nullable=True)
    caption = Column(String(500), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    property = relationship("Property", back_populates="media")

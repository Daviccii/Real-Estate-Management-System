from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class PropertySource(Base):
    __tablename__ = "property_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False, default="PROP_NOXA_VERIFIED")
    authorization_status = Column(String(50), nullable=False, default="approved")
    terms_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    properties = relationship("Property", back_populates="source")

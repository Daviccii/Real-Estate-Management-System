from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class PropertyTour(Base):
    """A 360°/virtual tour for a listing.

    `url` keeps the owner-supplied share link; `embed_url` is the canonical
    iframe URL rebuilt server-side by `tour_service.parse_tour_url()` from a
    strict provider allowlist. `embed_url` is NULL when the link is not
    embeddable — clients then only render it as an external link.
    """

    __tablename__ = "property_tours"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    url = Column(String(1000), nullable=False)
    provider = Column(String(50), nullable=False, default="link")
    embed_url = Column(String(1000), nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    property = relationship("Property", back_populates="tours")

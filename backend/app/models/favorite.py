from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    user = relationship("User", backref="favorites")
    property = relationship("Property", backref="favorites")

    # Ensure unique user-property combination
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='uq_user_property'),
    )
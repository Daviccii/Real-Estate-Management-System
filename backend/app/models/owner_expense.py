from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class OwnerExpense(Base):
    __tablename__ = "owner_expenses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(80), nullable=False)
    amount = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    expense_date = Column(DateTime, nullable=False, default=utc_now)
    status = Column(String(30), nullable=False, default="recorded")
    created_at = Column(DateTime, nullable=False, default=utc_now)

    owner = relationship("User", foreign_keys=[owner_id])
    property = relationship("Property", foreign_keys=[property_id])

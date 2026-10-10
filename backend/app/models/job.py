from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Index

from app.models.base import Base
from app.utils.time import utc_now


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="queued")
    attempts = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime, nullable=False, default=utc_now)
    locked_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_background_jobs_claim", "status", "available_at"),
    )

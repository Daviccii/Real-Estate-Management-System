import json
import logging
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.job import BackgroundJob
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


def enqueue_job(db: Session, job_type: str, payload: dict[str, Any], *, available_at=None) -> BackgroundJob:
    job = BackgroundJob(
        job_type=job_type,
        payload=json.dumps(payload),
        available_at=available_at or utc_now(),
    )
    db.add(job)
    db.flush()
    return job


def claim_job(db: Session) -> Optional[BackgroundJob]:
    job = (
        db.query(BackgroundJob)
        .filter(
            BackgroundJob.status == "queued",
            BackgroundJob.available_at <= utc_now(),
        )
        .order_by(BackgroundJob.id.asc())
        .with_for_update(skip_locked=True)
        .first()
    )
    if not job:
        return None
    job.status = "running"
    job.attempts += 1
    job.locked_at = utc_now()
    db.commit()
    return job


def complete_job(db: Session, job: BackgroundJob) -> None:
    job.status = "completed"
    job.completed_at = utc_now()
    job.locked_at = None
    db.commit()


def retry_job(db: Session, job: BackgroundJob, error: Exception, *, delay_seconds: int = 30) -> None:
    job.status = "queued"
    job.available_at = utc_now() + timedelta(seconds=delay_seconds)
    job.locked_at = None
    job.last_error = str(error)
    db.commit()
    logger.error("Background job failed; scheduled retry", extra={"job_id": job.id}, exc_info=True)

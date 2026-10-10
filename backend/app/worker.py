"""Durable background-job worker.

Run separately from the API process:
    python -m app.worker
"""

import json
import logging
import time

from app.database.database import SessionLocal
from app.services.job_service import claim_job, complete_job, retry_job
from app.services.job_handlers import HANDLERS

logger = logging.getLogger(__name__)


def handle_job(db, job_type: str, payload: dict) -> dict:
    handler = HANDLERS.get(job_type)
    if not handler:
        raise RuntimeError(f"No handler registered for background job type: {job_type}")
    return handler(db, payload)


def run() -> None:
    while True:
        db = SessionLocal()
        try:
            job = claim_job(db)
            if not job:
                time.sleep(1)
                continue
            try:
                job.result = json.dumps(handle_job(db, job.job_type, json.loads(job.payload)))
            except Exception as exc:
                retry_job(db, job, exc)
            else:
                complete_job(db, job)
        finally:
            db.close()


if __name__ == "__main__":
    run()

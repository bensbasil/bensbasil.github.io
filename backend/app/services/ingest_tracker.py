"""
Simple in-memory job tracker for long-running ingest tasks.
Resets on server restart — sufficient for a portfolio project.
"""

import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IngestJob:
    job_id: str
    topic: str
    user_id: str
    status: str = "started"         # started | running | done | failed
    total: int = 0
    completed: int = 0
    skipped: int = 0
    failed_count: int = 0
    papers: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    finished_at: Optional[str] = None


# Global in-memory store  { job_id → IngestJob }
_jobs: Dict[str, IngestJob] = {}


def create_job(topic: str, user_id: str) -> IngestJob:
    job_id = str(uuid.uuid4())
    job = IngestJob(job_id=job_id, topic=topic, user_id=user_id)
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[IngestJob]:
    return _jobs.get(job_id)


def to_dict(job: IngestJob) -> dict:
    return {
        "job_id": job.job_id,
        "topic": job.topic,
        "status": job.status,
        "total": job.total,
        "completed": job.completed,
        "skipped": job.skipped,
        "failed": job.failed_count,
        "papers": job.papers,
        "error": job.error,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }

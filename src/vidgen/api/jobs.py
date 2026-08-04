"""In-memory background job store for the API layer.

Rendering is slow (seconds to minutes), so an HTTP request never renders
inline — it submits a ``Job`` that runs on a background thread and is
polled via ``GET /jobs/{id}``. This module has no FastAPI/HTTP
dependency of its own; it is plain bookkeeping around a thread pool.
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

logger = logging.getLogger("vidgen.api")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    """The bookkeeping record for one submitted render."""

    id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    output_path: Path | None = None
    error: str | None = None


class JobStore:
    """Creates ``Job`` records and runs their work on a background thread pool."""

    def __init__(self, max_workers: int = 2) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, work: Callable[[str], Path]) -> Job:
        """Create a ``Job``, run ``work(job.id)`` in the background, and return immediately.

        ``work`` receives the new job's id so it can use it (e.g. as a
        default output filename) without a chicken-and-egg dependency on
        the ``Job`` object itself.
        """
        job = Job(id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run, job.id, work)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self, job_id: str, work: Callable[[str], Path]) -> None:
        with self._lock:
            self._jobs[job_id].status = JobStatus.RUNNING
        try:
            output_path = work(job_id)
        except Exception as exc:  # noqa: BLE001 - a failed job must not crash the pool
            logger.error("job %s failed: %s", job_id, exc)
            with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.FAILED
                job.error = str(exc)
            return
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.SUCCEEDED
            job.output_path = output_path

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)

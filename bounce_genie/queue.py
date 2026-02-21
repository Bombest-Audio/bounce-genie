"""
bounce_genie – job queue.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Deque, Iterator, List, Optional

from .models import BounceJob, JobStatus


class BounceQueue:
    """Thread-safe FIFO queue that holds and tracks BounceJob instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Deque[BounceJob] = deque()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, job: BounceJob) -> None:
        """Append *job* to the end of the queue."""
        with self._lock:
            self._jobs.append(job)

    def add_all(self, jobs: List[BounceJob]) -> None:
        """Append all *jobs* in order."""
        with self._lock:
            self._jobs.extend(jobs)

    def next_pending(self) -> Optional[BounceJob]:
        """Return and mark-as-in-progress the next PENDING job, or None."""
        with self._lock:
            for job in self._jobs:
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.IN_PROGRESS
                    return job
        return None

    def mark_completed(self, job: BounceJob) -> None:
        job.status = JobStatus.COMPLETED

    def mark_failed(self, job: BounceJob, error: str) -> None:
        job.status = JobStatus.FAILED
        job.error = error

    def mark_skipped(self, job: BounceJob, reason: str = "") -> None:
        job.status = JobStatus.SKIPPED
        job.error = reason

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs if j.status == JobStatus.PENDING)

    @property
    def all_jobs(self) -> List[BounceJob]:
        with self._lock:
            return list(self._jobs)

    @property
    def completed_jobs(self) -> List[BounceJob]:
        with self._lock:
            return [j for j in self._jobs if j.status == JobStatus.COMPLETED]

    @property
    def failed_jobs(self) -> List[BounceJob]:
        with self._lock:
            return [j for j in self._jobs if j.status == JobStatus.FAILED]

    def is_finished(self) -> bool:
        """True when no job is PENDING or IN_PROGRESS."""
        with self._lock:
            return all(
                j.status not in (JobStatus.PENDING, JobStatus.IN_PROGRESS)
                for j in self._jobs
            )

    def __len__(self) -> int:
        with self._lock:
            return len(self._jobs)

    def __iter__(self) -> Iterator[BounceJob]:
        with self._lock:
            return iter(list(self._jobs))

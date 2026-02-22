"""Job queue for managing pending BounceJob instances."""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Optional

from bounce_genie.models import BounceJob


class JobQueue:
    """Thread-safe FIFO queue of :class:`BounceJob` objects."""

    def __init__(self) -> None:
        self._queue: deque[BounceJob] = deque()
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, job: BounceJob) -> None:
        """Append *job* to the end of the queue."""
        with self._lock:
            self._queue.append(job)

    def add_many(self, jobs: list[BounceJob]) -> None:
        """Append multiple jobs in order."""
        with self._lock:
            self._queue.extend(jobs)

    def next(self) -> Optional[BounceJob]:
        """Remove and return the next job, or *None* if the queue is empty."""
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def clear(self) -> None:
        """Remove all pending jobs."""
        with self._lock:
            self._queue.clear()

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        with self._lock:
            return len(self._queue)

    def is_empty(self) -> bool:
        with self._lock:
            return not self._queue

    def peek(self) -> Optional[BounceJob]:
        """Return the next job without removing it."""
        with self._lock:
            return self._queue[0] if self._queue else None

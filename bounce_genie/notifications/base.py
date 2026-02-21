"""
bounce_genie.notifications.base – abstract notifier + batch summary.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..models import BounceJob


@dataclass
class BatchSummary:
    """A summary of a completed batch sent to notifiers."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    output_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def as_text(self) -> str:
        lines = [
            f"Bounce Genie batch complete.",
            f"  Total jobs : {self.total}",
            f"  Completed  : {self.completed}",
            f"  Failed     : {self.failed}",
        ]
        if self.output_files:
            lines.append(f"  Output files ({len(self.output_files)}):")
            for f in self.output_files:
                lines.append(f"    - {f}")
        if self.errors:
            lines.append("  Errors:")
            for e in self.errors:
                lines.append(f"    ! {e}")
        return "\n".join(lines)


class BaseNotifier(ABC):
    """Abstract base class for all notification backends."""

    @abstractmethod
    def notify(self, summary: BatchSummary, target: str) -> None:
        """
        Send a notification to *target* describing *summary*.

        Parameters
        ----------
        summary:
            The batch results.
        target:
            Backend-specific address (e.g. email address or phone number).
        """

    @abstractmethod
    def notify_job_complete(self, job: BounceJob) -> None:
        """Send a per-job completion notification if configured."""

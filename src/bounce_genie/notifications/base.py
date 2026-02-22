"""Abstract base class for notifiers, plus shared data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BatchResult:
    """Summary of a completed batch bounce run."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.succeeded / self.total

    def summary_text(self) -> str:
        lines = [
            f"Bounce Genie – batch complete",
            f"  Jobs: {self.total}  ✓ {self.succeeded}  ✗ {self.failed}",
        ]
        if self.outputs:
            lines.append(f"  Output files ({len(self.outputs)}):")
            for path in self.outputs:
                lines.append(f"    • {path}")
        if self.errors:
            lines.append(f"  Errors:")
            for err in self.errors:
                lines.append(f"    • {err}")
        return "\n".join(lines)


class BaseNotifier(ABC):
    """Interface for sending batch-completion notifications."""

    @abstractmethod
    def send(self, result: BatchResult, recipient: str) -> None:
        """Send *result* summary to *recipient*.

        Parameters
        ----------
        result:
            The completed batch summary.
        recipient:
            Destination address (email address or phone number).
        """

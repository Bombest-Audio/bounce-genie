"""Abstract base class (interface) for DAW adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy


class IDawAdapter(ABC):
    """Interface that every DAW adapter must implement.

    Each concrete adapter encapsulates the UI automation logic for one
    specific DAW, keeping the rest of the system DAW-agnostic.
    """

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def open_session(self, path: Path) -> None:
        """Open (or bring to focus) the DAW session at *path*."""

    @abstractmethod
    def close_session(self) -> None:
        """Close the current session without saving."""

    # ------------------------------------------------------------------
    # Bounce workflow
    # ------------------------------------------------------------------

    @abstractmethod
    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        """Apply *selection_strategy* and configure bounce settings."""

    @abstractmethod
    def execute_bounce(self, options: BounceOptions) -> None:
        """Trigger the actual bounce/export and wait until it completes."""

    @abstractmethod
    def detect_outputs(self, job: BounceJob) -> list[Path]:
        """Return the list of output files produced by the most recent bounce."""

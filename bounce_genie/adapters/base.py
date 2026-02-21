"""
bounce_genie.adapters.base – IDawAdapter abstract interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..models import BounceJob, BounceOptions, SelectionStrategy


class IDawAdapter(ABC):
    """
    Abstract interface every DAW adapter must implement.

    Implementations drive the actual DAW (via the automation engine) to
    open a session, configure the bounce dialog, execute the bounce, and
    report the resulting output files.
    """

    # Override in subclass to declare which file extensions belong to this DAW.
    SESSION_EXTENSIONS: tuple[str, ...] = ()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def open_session(self, path: Path) -> None:
        """
        Open (or bring to focus) the session at *path* inside the DAW.

        Raises
        ------
        FileNotFoundError
            If *path* does not exist.
        RuntimeError
            If the DAW fails to open the session.
        """

    @abstractmethod
    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        """
        Prepare the DAW's bounce/export dialog with the given *options*.

        This may involve setting the time selection, choosing formats,
        choosing online/offline mode, etc., but does **not** start the
        bounce yet.
        """

    @abstractmethod
    def execute_bounce(self, options: BounceOptions) -> None:
        """
        Confirm and execute the bounce.

        Blocks (or polls) until the DAW reports completion.

        Raises
        ------
        RuntimeError
            If the bounce fails or times out.
        """

    @abstractmethod
    def detect_outputs(self, job: BounceJob) -> List[Path]:
        """
        Return the list of output files produced for *job*.

        The detector may inspect the DAW's default bounce folder, compare
        file timestamps, etc.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def can_handle(self, session_path: Path) -> bool:
        """Return True if this adapter recognises *session_path*'s extension."""
        return session_path.suffix.lower() in self.SESSION_EXTENSIONS

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{type(self).__name__}>"

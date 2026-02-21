"""
bounce_genie.adapters.cubase – Cubase DAW adapter.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from ..models import BounceJob, BounceOptions, SelectionStrategy
from .base import IDawAdapter

logger = logging.getLogger(__name__)


class CubaseAdapter(IDawAdapter):
    """
    Adapter for Steinberg Cubase sessions (.cpr).

    Cubase bounce behavior:
    - Default selection strategy: TRIMMED_COPY (similar to Logic; save a
      project copy trimmed to the export cycle marker).
    - Export triggered via File → Export → Audio Mixdown.
    """

    SESSION_EXTENSIONS = (".cpr",)

    def __init__(self, automation_engine=None) -> None:
        self._engine = automation_engine

    def open_session(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {path}")
        logger.info("Cubase: opening session %s", path)
        if self._engine:
            self._engine.open_application("Cubase")
            self._engine.open_file(path)

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info(
            "Cubase: prepping bounce | strategy=%s formats=%s",
            selection_strategy,
            options.formats,
        )
        if self._engine:
            self._engine.open_menu("File", "Export", "Audio Mixdown…")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Cubase: executing bounce")
        if self._engine:
            self._engine.click_button("Export")

    def detect_outputs(self, job: BounceJob) -> List[Path]:
        bounce_dir = job.session_path.parent / "Audio"
        if not bounce_dir.exists():
            logger.warning("Cubase: export folder not found: %s", bounce_dir)
            return []
        files = sorted(bounce_dir.iterdir())
        logger.info("Cubase: detected %d output file(s)", len(files))
        return files

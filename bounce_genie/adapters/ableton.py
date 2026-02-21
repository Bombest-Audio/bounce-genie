"""
bounce_genie.adapters.ableton – Ableton Live DAW adapter.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from ..models import BounceJob, BounceOptions, SelectionStrategy
from .base import IDawAdapter

logger = logging.getLogger(__name__)


class AbletonAdapter(IDawAdapter):
    """
    Adapter for Ableton Live sets (.als).

    Ableton bounce behavior:
    - Default selection strategy: TRIMMED_COPY (save a project copy trimmed
      to the export length / locators before bouncing).
    - Export triggered via File → Export Audio/Video.
    """

    SESSION_EXTENSIONS = (".als",)

    def __init__(self, automation_engine=None) -> None:
        self._engine = automation_engine

    def open_session(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {path}")
        logger.info("Ableton: opening session %s", path)
        if self._engine:
            self._engine.open_application("Ableton Live")
            self._engine.open_file(path)

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info(
            "Ableton: prepping bounce | strategy=%s formats=%s",
            selection_strategy,
            options.formats,
        )
        if self._engine:
            self._engine.open_menu("File", "Export Audio/Video…")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Ableton: executing bounce")
        if self._engine:
            self._engine.click_button("Export")

    def detect_outputs(self, job: BounceJob) -> List[Path]:
        bounce_dir = job.session_path.parent
        if not bounce_dir.exists():
            return []
        files = [
            p for p in sorted(bounce_dir.iterdir())
            if p.suffix.lower() in (".wav", ".aiff", ".mp3", ".aac", ".flac")
        ]
        logger.info("Ableton: detected %d output file(s)", len(files))
        return files

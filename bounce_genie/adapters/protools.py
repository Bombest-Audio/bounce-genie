"""
bounce_genie.adapters.protools – Pro Tools DAW adapter.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from ..models import BounceJob, BounceOptions, SelectionStrategy
from .base import IDawAdapter

logger = logging.getLogger(__name__)


class ProToolsAdapter(IDawAdapter):
    """
    Adapter for Pro Tools sessions (.ptx / .pts).

    Pro Tools bounce behavior:
    - Default selection strategy: USE_SAVED_SELECTION (the saved timeline
      selection is used for the bounce range).
    - Falls back to SELECT_ALL when no selection is detected.
    - Multiple formats (e.g. WAV + MP3) produce separate output files per song.
    - Supports offline (faster-than-real-time) bouncing.
    """

    SESSION_EXTENSIONS = (".ptx", ".pts")

    def __init__(self, automation_engine=None) -> None:
        self._engine = automation_engine

    def open_session(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {path}")
        logger.info("ProTools: opening session %s", path)
        if self._engine:
            self._engine.open_application("Pro Tools")
            self._engine.open_file(path)

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info(
            "ProTools: prepping bounce | strategy=%s formats=%s offline=%s",
            selection_strategy,
            options.formats,
            options.offline,
        )
        if selection_strategy == SelectionStrategy.SELECT_ALL:
            if self._engine:
                self._engine.send_shortcut("cmd+a")  # select all

        if self._engine:
            self._engine.open_menu("File", "Bounce Mix…")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("ProTools: executing bounce")
        if self._engine:
            self._engine.click_button("Bounce")

    def detect_outputs(self, job: BounceJob) -> List[Path]:
        bounce_dir = job.session_path.parent / "Bounced Files"
        if not bounce_dir.exists():
            logger.warning("ProTools: bounce folder not found: %s", bounce_dir)
            return []
        files = sorted(bounce_dir.iterdir())
        logger.info("ProTools: detected %d output file(s)", len(files))
        return files

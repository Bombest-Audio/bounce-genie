"""
bounce_genie.adapters.logic – Logic Pro X DAW adapter.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from ..models import BounceJob, BounceOptions, SelectionStrategy
from .base import IDawAdapter

logger = logging.getLogger(__name__)


class LogicAdapter(IDawAdapter):
    """
    Adapter for Logic Pro X sessions (.logicx).

    Logic bounce behavior:
    - Default selection strategy: TRIMMED_COPY (saves a project copy trimmed
      to the desired bounce length before export to avoid tail issues).
    - Bounce is triggered via File → Bounce → Project or Section.
    """

    SESSION_EXTENSIONS = (".logicx",)

    def __init__(self, automation_engine=None) -> None:
        self._engine = automation_engine

    def open_session(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {path}")
        logger.info("Logic: opening session %s", path)
        if self._engine:
            self._engine.open_application("Logic Pro X")
            self._engine.open_file(path)

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info(
            "Logic: prepping bounce | strategy=%s formats=%s",
            selection_strategy,
            options.formats,
        )
        if selection_strategy == SelectionStrategy.TRIMMED_COPY and self._engine:
            self._engine.open_menu("File", "Save As…")  # save trimmed copy first

        if self._engine:
            self._engine.open_menu("File", "Bounce", "Project or Section…")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Logic: executing bounce")
        if self._engine:
            self._engine.click_button("Bounce")

    def detect_outputs(self, job: BounceJob) -> List[Path]:
        bounce_dir = job.session_path.parent / "Bounces"
        if not bounce_dir.exists():
            logger.warning("Logic: bounce folder not found: %s", bounce_dir)
            return []
        files = sorted(bounce_dir.iterdir())
        logger.info("Logic: detected %d output file(s)", len(files))
        return files

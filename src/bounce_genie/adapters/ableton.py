"""Ableton Live DAW adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.automation.engine import AutomationEngine
from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy

logger = logging.getLogger(__name__)


class AbletonAdapter(IDawAdapter):
    """Automates Ableton Live on macOS.

    Ableton export workflow:
    1. Open the Live Set file (.als).
    2. Set the export range (Loop Brace) as needed.
    3. Use File > Export Audio/Video… (Cmd+Shift+R).
    4. Configure format/destination and click Export.
    """

    APP_NAME = "Ableton Live"

    def __init__(self, engine: AutomationEngine | None = None) -> None:
        self._engine = engine or AutomationEngine()

    # ------------------------------------------------------------------
    # IDawAdapter implementation
    # ------------------------------------------------------------------

    def open_session(self, path: Path) -> None:
        logger.info("Ableton: opening set %s", path)
        self._engine.launch_app(self.APP_NAME)
        self._engine.open_file(path)

    def close_session(self) -> None:
        logger.info("Ableton: closing set")
        self._engine.menu_action(self.APP_NAME, ["File", "Close"])

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info("Ableton: prep bounce with strategy %s", selection_strategy)
        if selection_strategy == SelectionStrategy.SELECT_ALL:
            self._engine.key_combo(["command", "a"])
        elif selection_strategy == SelectionStrategy.TRIMMED_COPY:
            self._engine.menu_action(self.APP_NAME, ["File", "Save a Copy…"])
            self._engine.wait_for_window("Save a Copy", timeout=15)
            self._engine.click_button("Save")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Ableton: executing export")
        self._engine.key_combo(["command", "shift", "r"])
        self._engine.wait_for_window("Export Audio/Video", timeout=30)
        self._engine.click_button("Export")
        self._engine.wait_for_window_gone("Export Audio/Video", timeout=3600)

    def detect_outputs(self, job: BounceJob) -> list[Path]:
        export_folder = job.session_path.parent
        if not export_folder.exists():
            return []
        return sorted(
            p for p in export_folder.iterdir()
            if p.suffix.lower() in {".wav", ".aiff", ".mp3", ".flac"}
        )

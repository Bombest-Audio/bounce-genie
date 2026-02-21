"""Cubase DAW adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.automation.engine import AutomationEngine
from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy

logger = logging.getLogger(__name__)


class CubaseAdapter(IDawAdapter):
    """Automates Steinberg Cubase on macOS.

    Cubase export workflow:
    1. Open the project file.
    2. Set the export range (Locators) via Edit menu or key commands.
    3. Use File > Export > Audio Mixdown… (Cmd+Shift+E).
    4. Configure format/destination and click Export.
    """

    APP_NAME = "Cubase"

    def __init__(self, engine: AutomationEngine | None = None) -> None:
        self._engine = engine or AutomationEngine()

    # ------------------------------------------------------------------
    # IDawAdapter implementation
    # ------------------------------------------------------------------

    def open_session(self, path: Path) -> None:
        logger.info("Cubase: opening project %s", path)
        self._engine.launch_app(self.APP_NAME)
        self._engine.open_file(path)

    def close_session(self) -> None:
        logger.info("Cubase: closing project")
        self._engine.menu_action(self.APP_NAME, ["File", "Close"])

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info("Cubase: prep bounce with strategy %s", selection_strategy)
        if selection_strategy == SelectionStrategy.SELECT_ALL:
            self._engine.key_combo(["command", "a"])
        elif selection_strategy == SelectionStrategy.TRIMMED_COPY:
            self._engine.menu_action(self.APP_NAME, ["File", "Save New Version"])

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Cubase: executing export")
        self._engine.key_combo(["command", "shift", "e"])
        self._engine.wait_for_window("Export Audio Mixdown", timeout=30)
        self._engine.click_button("Export Audio")
        self._engine.wait_for_window_gone("Export Audio Mixdown", timeout=3600)

    def detect_outputs(self, job: BounceJob) -> list[Path]:
        export_folder = job.session_path.parent / "Exports"
        if not export_folder.exists():
            logger.warning("Cubase export folder not found: %s", export_folder)
            return []
        return sorted(export_folder.iterdir())

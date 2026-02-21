"""Logic Pro X DAW adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.automation.engine import AutomationEngine
from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy

logger = logging.getLogger(__name__)


class LogicAdapter(IDawAdapter):
    """Automates Apple Logic Pro X on macOS.

    Logic bounce workflow:
    1. Open the project file.
    2. For ``TRIMMED_COPY``: save a copy trimmed to the playback region.
    3. Use File > Bounce > Project or Section… (Ctrl+B or Cmd+B depending on version).
    4. Configure format/destination in the Bounce dialog.
    5. Click Bounce.
    """

    APP_NAME = "Logic Pro X"

    def __init__(self, engine: AutomationEngine | None = None) -> None:
        self._engine = engine or AutomationEngine()

    # ------------------------------------------------------------------
    # IDawAdapter implementation
    # ------------------------------------------------------------------

    def open_session(self, path: Path) -> None:
        logger.info("Logic Pro: opening project %s", path)
        self._engine.launch_app(self.APP_NAME)
        self._engine.open_file(path)

    def close_session(self) -> None:
        logger.info("Logic Pro: closing project")
        self._engine.menu_action(self.APP_NAME, ["File", "Close Project"])

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info("Logic Pro: prep bounce with strategy %s", selection_strategy)
        if selection_strategy == SelectionStrategy.SELECT_ALL:
            self._engine.key_combo(["command", "a"])
        elif selection_strategy == SelectionStrategy.TRIMMED_COPY:
            self._engine.menu_action(self.APP_NAME, ["File", "Save a Copy As…"])
            self._engine.wait_for_window("Save a Copy As", timeout=15)
            self._engine.click_button("Save")

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Logic Pro: executing bounce")
        self._engine.menu_action(self.APP_NAME, ["File", "Bounce", "Project or Section…"])
        self._engine.wait_for_window("Bounce", timeout=30)
        self._engine.click_button("Bounce")
        self._engine.wait_for_window_gone("Bounce", timeout=3600)

    def detect_outputs(self, job: BounceJob) -> list[Path]:
        bounce_folder = job.session_path.parent / "Bounces"
        if not bounce_folder.exists():
            logger.warning("Logic bounce folder not found: %s", bounce_folder)
            return []
        return sorted(bounce_folder.iterdir())

"""Pro Tools DAW adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.automation.engine import AutomationEngine
from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy

logger = logging.getLogger(__name__)


class ProToolsAdapter(IDawAdapter):
    """Automates Avid Pro Tools on macOS.

    Pro Tools bounce workflow:
    1. Open the session file (File > Open Session).
    2. Depending on *selection_strategy*:
       - ``USE_SAVED_SELECTION``: use the saved selection range.
       - ``SELECT_ALL``: Cmd+A to select all.
       - ``TRIMMED_COPY``: not used; falls back to ``SELECT_ALL``.
    3. Open the Bounce Mix dialog (File > Bounce Mix…).
    4. Configure format options.
    5. Click Bounce.
    """

    BOUNCE_FOLDER_NAME = "Bounced Files"
    APP_NAME = "Pro Tools"

    def __init__(self, engine: AutomationEngine | None = None) -> None:
        self._engine = engine or AutomationEngine()

    # ------------------------------------------------------------------
    # IDawAdapter implementation
    # ------------------------------------------------------------------

    def open_session(self, path: Path) -> None:
        logger.info("Pro Tools: opening session %s", path)
        self._engine.launch_app(self.APP_NAME)
        self._engine.open_file(path)

    def close_session(self) -> None:
        logger.info("Pro Tools: closing session")
        self._engine.menu_action(self.APP_NAME, ["File", "Close Session"])

    def prep_bounce(
        self,
        selection_strategy: SelectionStrategy,
        options: BounceOptions,
    ) -> None:
        logger.info("Pro Tools: prep bounce with strategy %s", selection_strategy)
        if selection_strategy in (
            SelectionStrategy.SELECT_ALL,
            SelectionStrategy.TRIMMED_COPY,
        ):
            self._engine.key_combo(["command", "a"])

    def execute_bounce(self, options: BounceOptions) -> None:
        logger.info("Pro Tools: executing bounce")
        self._engine.menu_action(self.APP_NAME, ["File", "Bounce Mix…"])
        # Wait for the Bounce Mix dialog and confirm
        self._engine.wait_for_window("Bounce Mix", timeout=30)
        self._engine.click_button("Bounce")
        self._engine.wait_for_window_gone("Bounce Mix", timeout=3600)

    def detect_outputs(self, job: BounceJob) -> list[Path]:
        bounce_folder = job.session_path.parent / self.BOUNCE_FOLDER_NAME
        if not bounce_folder.exists():
            logger.warning("Pro Tools bounce folder not found: %s", bounce_folder)
            return []
        return sorted(bounce_folder.iterdir())

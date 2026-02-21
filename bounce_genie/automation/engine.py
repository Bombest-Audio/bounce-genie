"""
bounce_genie.automation.engine – macOS-first UI automation engine.

Drives mouse/keyboard to interact with DAW applications.  All operations
are intended to be called by DAW adapters, not directly by end-user code.

On macOS this would use the Accessibility API (via ``pyobjc`` or
``atomacos``).  The implementation here provides a clean interface with
stub bodies so that:
  - unit tests can mock / subclass without needing a real macOS display.
  - future platform backends (Windows) can be plugged in by subclassing.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0      # seconds to wait for a UI element
_DEFAULT_POLL_INTERVAL = 0.5  # seconds between polling attempts


class AutomationError(RuntimeError):
    """Raised when an automation step fails or times out."""


class AutomationEngine:
    """
    Drives a DAW application's UI via macOS Accessibility APIs.

    Parameters
    ----------
    timeout:
        How long (in seconds) to wait for expected UI elements before
        raising :class:`AutomationError`.
    poll_interval:
        How frequently (in seconds) to poll for expected elements.
    dry_run:
        When *True* all actions are logged but not actually executed.
        Useful for testing and development.
    """

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        dry_run: bool = False,
    ) -> None:
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # Application management
    # ------------------------------------------------------------------

    def open_application(self, app_name: str) -> None:
        """Launch *app_name* or bring it to front if already running."""
        logger.info("[automation] open_application(%r)", app_name)
        if self.dry_run:
            return
        self._macos_open_application(app_name)

    def open_file(self, path: Path) -> None:
        """Ask the front-most application to open *path*."""
        logger.info("[automation] open_file(%s)", path)
        if self.dry_run:
            return
        self._macos_open_file(path)

    # ------------------------------------------------------------------
    # Menu navigation
    # ------------------------------------------------------------------

    def open_menu(self, *menu_path: str) -> None:
        """
        Navigate through the menu bar.

        Example: ``open_menu("File", "Bounce", "Project or Section…")``
        """
        logger.info("[automation] open_menu(%s)", " → ".join(menu_path))
        if self.dry_run:
            return
        self._macos_click_menu(*menu_path)

    # ------------------------------------------------------------------
    # UI element interaction
    # ------------------------------------------------------------------

    def click_button(self, label: str) -> None:
        """Click the button identified by *label* in the frontmost dialog."""
        logger.info("[automation] click_button(%r)", label)
        if self.dry_run:
            return
        self._macos_click_button(label)

    def send_shortcut(self, shortcut: str) -> None:
        """
        Send a keyboard shortcut.

        *shortcut* uses a simple notation: modifiers separated by ``+``
        followed by the key name, e.g. ``"cmd+a"``, ``"cmd+shift+b"``.
        """
        logger.info("[automation] send_shortcut(%r)", shortcut)
        if self.dry_run:
            return
        self._macos_send_shortcut(shortcut)

    def wait_for_element(
        self,
        identifier: str,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Block until the UI element identified by *identifier* is visible.

        Raises :class:`AutomationError` on timeout.
        """
        deadline = time.monotonic() + (timeout or self.timeout)
        logger.info("[automation] wait_for_element(%r)", identifier)
        while time.monotonic() < deadline:
            if self.dry_run or self._macos_element_exists(identifier):
                return
            time.sleep(self.poll_interval)
        raise AutomationError(
            f"Timed out waiting for UI element {identifier!r} "
            f"after {timeout or self.timeout:.1f}s"
        )

    # ------------------------------------------------------------------
    # macOS-specific private stubs (override in integration tests/platform)
    # ------------------------------------------------------------------

    def _macos_open_application(self, app_name: str) -> None:  # pragma: no cover
        import subprocess
        subprocess.run(["open", "-a", app_name], check=True)

    def _macos_open_file(self, path: Path) -> None:  # pragma: no cover
        import subprocess
        subprocess.run(["open", str(path)], check=True)

    def _macos_click_menu(self, *menu_path: str) -> None:  # pragma: no cover
        raise NotImplementedError(
            "macOS Accessibility integration not yet implemented. "
            "Install `atomacos` and subclass AutomationEngine."
        )

    def _macos_click_button(self, label: str) -> None:  # pragma: no cover
        raise NotImplementedError(
            "macOS Accessibility integration not yet implemented."
        )

    def _macos_send_shortcut(self, shortcut: str) -> None:  # pragma: no cover
        raise NotImplementedError(
            "macOS Accessibility integration not yet implemented."
        )

    def _macos_element_exists(self, identifier: str) -> bool:  # pragma: no cover
        raise NotImplementedError(
            "macOS Accessibility integration not yet implemented."
        )

"""macOS UI automation engine.

Uses the ``subprocess``-based ``osascript`` (AppleScript) and the
``pyobjc`` accessibility APIs when available, with a plain stub fallback
so that unit tests can run on any platform without macOS-specific
dependencies.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_IS_MACOS = platform.system() == "Darwin"


class AutomationError(RuntimeError):
    """Raised when a UI automation action cannot be completed."""


class AutomationEngine:
    """Drives macOS application UIs via AppleScript / accessibility APIs.

    On non-macOS platforms (or when ``dry_run=True``) every method is a
    no-op and only logs what it *would* have done.  This allows the rest
    of the codebase (and the test suite) to import and unit-test without
    macOS-specific dependencies.

    Parameters
    ----------
    dry_run:
        When *True*, no real UI actions are taken; everything is logged at
        DEBUG level instead.  Useful for testing and CI.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run or not _IS_MACOS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _applescript(self, script: str) -> str:
        """Run an AppleScript snippet and return stdout."""
        if self.dry_run:
            logger.debug("applescript (dry-run): %s", script)
            return ""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AutomationError(
                f"AppleScript error: {result.stderr.strip()!r} for script: {script!r}"
            )
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def launch_app(self, app_name: str) -> None:
        """Bring *app_name* to the foreground, launching it if necessary."""
        logger.debug("Launching/focusing app: %s", app_name)
        self._applescript(f'tell application "{app_name}" to activate')

    def open_file(self, path: Path) -> None:
        """Open *path* in the currently active application."""
        logger.debug("Opening file: %s", path)
        self._applescript(
            f'tell application "Finder" to open POSIX file "{path}"'
        )
        time.sleep(2)  # give the DAW time to load the session

    def menu_action(self, app_name: str, menu_path: list[str]) -> None:
        """Activate a menu item by navigating *menu_path* inside *app_name*."""
        logger.debug("Menu action %s → %s", app_name, " > ".join(menu_path))
        if len(menu_path) < 2:
            raise ValueError("menu_path must have at least two elements (menu, item)")
        menu, *items = menu_path
        # Build nested 'menu item' AppleScript reference
        ref = " of ".join(
            [f'menu item "{i}"' for i in reversed(items)]
            + [f'menu "{menu}" of menu bar 1']
        )
        script = (
            f'tell application "System Events"\n'
            f'  tell process "{app_name}"\n'
            f'    click {ref}\n'
            f'  end tell\n'
            f'end tell'
        )
        self._applescript(script)

    def key_combo(self, keys: list[str]) -> None:
        """Press a key combination, e.g. ``["command", "a"]``."""
        logger.debug("Key combo: %s", "+".join(keys))
        modifiers = keys[:-1]
        key = keys[-1]
        mod_str = ", ".join(f'"{m}"' for m in modifiers)
        script = (
            f'tell application "System Events"\n'
            f'  keystroke "{key}" using {{{mod_str} down}}\n'
            f'end tell'
        )
        self._applescript(script)

    def click_button(self, button_name: str) -> None:
        """Click the first button matching *button_name* in the front window."""
        logger.debug("Clicking button: %s", button_name)
        script = (
            f'tell application "System Events"\n'
            f'  click button "{button_name}" of front window of '
            f'(first process whose frontmost is true)\n'
            f'end tell'
        )
        self._applescript(script)

    def wait_for_window(self, window_name: str, timeout: float = 30) -> None:
        """Block until a window named *window_name* appears or *timeout* expires."""
        logger.debug("Waiting for window: %s (timeout=%ss)", window_name, timeout)
        if self.dry_run:
            return
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            script = (
                f'tell application "System Events"\n'
                f'  set w to every window of (first process whose frontmost is true)\n'
                f'  set names to name of every item of w\n'
                f'  if "{window_name}" is in names then return true\n'
                f'end tell\n'
                f'return false'
            )
            result = self._applescript(script)
            if result == "true":
                return
            time.sleep(0.5)
        raise AutomationError(
            f"Timed out waiting for window '{window_name}' after {timeout}s"
        )

    def wait_for_window_gone(self, window_name: str, timeout: float = 3600) -> None:
        """Block until the window named *window_name* closes or *timeout* expires."""
        logger.debug("Waiting for window to close: %s (timeout=%ss)", window_name, timeout)
        if self.dry_run:
            return
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            script = (
                f'tell application "System Events"\n'
                f'  set w to every window of (first process whose frontmost is true)\n'
                f'  set names to name of every item of w\n'
                f'  if "{window_name}" is not in names then return true\n'
                f'end tell\n'
                f'return false'
            )
            result = self._applescript(script)
            if result == "true":
                return
            time.sleep(1)
        raise AutomationError(
            f"Timed out waiting for window '{window_name}' to close after {timeout}s"
        )

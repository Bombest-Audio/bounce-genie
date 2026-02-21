"""Bounce output detector – watches DAW bounce folders for new files."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# watchdog is an optional dependency at import time so we can fall back
# gracefully in environments where it isn't installed.
try:
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    from watchdog.observers import Observer
    _HAS_WATCHDOG = True
except ImportError:  # pragma: no cover
    _HAS_WATCHDOG = False


OutputCallback = Callable[[Path], None]


class _NewFileHandler:
    """Thin adapter between watchdog events and an :data:`OutputCallback`."""

    def __init__(self, callback: OutputCallback, suffixes: set[str]) -> None:
        self._callback = callback
        self._suffixes = suffixes

    # watchdog calls dispatch() on us for every event
    def dispatch(self, event: "FileSystemEvent") -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in self._suffixes:
            logger.debug("Detected new output file: %s", path)
            self._callback(path)


class BounceOutputDetector:
    """Watches one or more directories for newly created audio files.

    Parameters
    ----------
    directories:
        The paths to watch (created if they don't exist).
    callback:
        Called with the :class:`~pathlib.Path` of each new audio file.
    suffixes:
        File extensions to treat as audio outputs.  Defaults to the most
        common audio formats.
    """

    DEFAULT_SUFFIXES = {".wav", ".aiff", ".aif", ".mp3", ".flac"}

    def __init__(
        self,
        directories: list[Path],
        callback: OutputCallback,
        suffixes: set[str] | None = None,
    ) -> None:
        self._directories = [Path(d) for d in directories]
        self._callback = callback
        self._suffixes = suffixes or self.DEFAULT_SUFFIXES
        self._observer: "Observer | None" = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin watching all configured directories."""
        if not _HAS_WATCHDOG:
            logger.warning(
                "watchdog is not installed – BounceOutputDetector is a no-op. "
                "Install it with: pip install watchdog"
            )
            return

        from watchdog.observers import Observer  # noqa: PLC0415

        handler = _NewFileHandler(self._callback, self._suffixes)
        self._observer = Observer()
        for directory in self._directories:
            directory.mkdir(parents=True, exist_ok=True)
            self._observer.schedule(handler, str(directory), recursive=False)
        self._observer.start()
        logger.info("BounceOutputDetector started watching: %s", self._directories)

    def stop(self) -> None:
        """Stop watching."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("BounceOutputDetector stopped")

    def __enter__(self) -> "BounceOutputDetector":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

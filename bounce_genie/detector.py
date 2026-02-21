"""
bounce_genie.detector – Bounce Output Detector.

Watches one or more directories for new audio files that appear after a
bounce starts.  Uses ``watchdog`` for filesystem events.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional, Set

try:
    from watchdog.events import FileCreatedEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    _WATCHDOG_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)

_AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {".wav", ".aiff", ".aif", ".mp3", ".aac", ".flac", ".m4a"}
)


class BounceOutputDetector:
    """
    Watches a directory for newly created audio files.

    Usage
    -----
    ::

        detector = BounceOutputDetector("/path/to/bounces")
        detector.start()
        # ... trigger bounce ...
        new_files = detector.wait_for_new_files(timeout=120)
        detector.stop()

    Parameters
    ----------
    watch_dir:
        The directory to monitor.
    audio_extensions:
        Set of file extensions (including the leading dot) to track.
        Defaults to :data:`_AUDIO_EXTENSIONS`.
    """

    def __init__(
        self,
        watch_dir: Path,
        audio_extensions: Optional[Set[str]] = None,
    ) -> None:
        self.watch_dir = Path(watch_dir)
        self.audio_extensions = audio_extensions or _AUDIO_EXTENSIONS
        self._new_files: List[Path] = []
        self._lock = threading.Lock()
        self._observer: Optional[object] = None
        self._baseline: Set[Path] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Snapshot the current directory state and begin watching.

        Must be called **before** triggering the bounce so that files
        created by the bounce are detected as "new".
        """
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self._baseline = self._current_audio_files()
        self._new_files.clear()

        if not _WATCHDOG_AVAILABLE:
            logger.warning(
                "watchdog is not installed; BounceOutputDetector will use "
                "polling via wait_for_new_files instead of filesystem events."
            )
            return

        handler = _AudioFileHandler(
            audio_extensions=self.audio_extensions,
            on_created=self._on_file_created,
        )
        self._observer = Observer()
        self._observer.schedule(handler, str(self.watch_dir), recursive=False)  # type: ignore[union-attr]
        self._observer.start()  # type: ignore[union-attr]
        logger.info("BounceOutputDetector: watching %s", self.watch_dir)

    def stop(self) -> None:
        """Stop the filesystem observer."""
        if self._observer is not None:
            self._observer.stop()  # type: ignore[union-attr]
            self._observer.join()  # type: ignore[union-attr]
            self._observer = None
            logger.info("BounceOutputDetector: stopped")

    # ------------------------------------------------------------------
    # Waiting / polling
    # ------------------------------------------------------------------

    def wait_for_new_files(
        self,
        timeout: float = 120.0,
        poll_interval: float = 1.0,
        on_progress: Optional[Callable[[List[Path]], None]] = None,
    ) -> List[Path]:
        """
        Block until at least one new audio file appears (or *timeout* elapses).

        Falls back to polling when watchdog is unavailable.

        Parameters
        ----------
        timeout:
            Maximum seconds to wait.
        poll_interval:
            Seconds between directory scans (polling fallback).
        on_progress:
            Optional callback invoked each time new files are discovered.

        Returns
        -------
        List[Path]
            All new audio files discovered since :meth:`start` was called.
            Returns an empty list on timeout.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            current = self._current_audio_files()
            new = sorted(current - self._baseline)
            if new:
                with self._lock:
                    for f in new:
                        if f not in self._new_files:
                            self._new_files.append(f)
                if on_progress:
                    on_progress(new)
                break
            time.sleep(poll_interval)

        with self._lock:
            return list(self._new_files)

    def get_new_files(self) -> List[Path]:
        """Return all new files discovered so far (non-blocking)."""
        with self._lock:
            return list(self._new_files)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _current_audio_files(self) -> Set[Path]:
        if not self.watch_dir.exists():
            return set()
        return {
            p
            for p in self.watch_dir.iterdir()
            if p.is_file() and p.suffix.lower() in self.audio_extensions
        }

    def _on_file_created(self, path: Path) -> None:
        with self._lock:
            if path not in self._new_files:
                self._new_files.append(path)
                logger.info("BounceOutputDetector: new file detected: %s", path)


if _WATCHDOG_AVAILABLE:
    class _AudioFileHandler(FileSystemEventHandler):
        def __init__(
            self,
            audio_extensions: frozenset[str],
            on_created: Callable[[Path], None],
        ) -> None:
            super().__init__()
            self._audio_extensions = audio_extensions
            self._on_created = on_created

        def on_created(self, event: FileCreatedEvent) -> None:
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() in self._audio_extensions:
                self._on_created(path)

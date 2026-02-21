"""
bounce_genie.naming – Template-based naming and file routing engine.

Naming templates support the following placeholders:

    {session_name}   – stem of the session file
    {format}         – audio format extension (e.g. "wav", "mp3")
    {index}          – zero-padded position of this job in the batch (e.g. "01")
    {date}           – ISO date of the bounce (YYYY-MM-DD)
    {time}           – 24 h time of the bounce (HHMMSS)

Example templates
-----------------
- ``"{session_name}"``       → ``"MySong"``
- ``"{session_name}_{format}"`` → ``"MySong_wav"``
- ``"{index:02d}_{session_name}"`` → ``"01_MySong"``
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import AudioFormat, BounceJob

logger = logging.getLogger(__name__)


class NamingEngine:
    """
    Resolves the output filename for a bounce job.

    Parameters
    ----------
    job:
        The :class:`~bounce_genie.models.BounceJob` being processed.
    fmt:
        The target :class:`~bounce_genie.models.AudioFormat` (relevant
        when the job produces multiple formats).
    batch_index:
        Zero-based position of this job in the batch queue.
    now:
        Override the current datetime (useful in tests).
    """

    def __init__(
        self,
        job: BounceJob,
        fmt: Optional[AudioFormat] = None,
        batch_index: int = 0,
        now: Optional[datetime] = None,
    ) -> None:
        self._job = job
        self._fmt = fmt
        self._index = batch_index
        self._now = now or datetime.now()

    def resolve(self) -> str:
        """Return the final filename stem (without extension)."""
        template = self._job.naming_template
        context = {
            "session_name": self._job.session_name,
            "format": self._fmt.value if self._fmt else "",
            "index": self._index,
            "date": self._now.strftime("%Y-%m-%d"),
            "time": self._now.strftime("%H%M%S"),
        }
        try:
            return template.format(**context)
        except KeyError as exc:
            raise ValueError(
                f"Unknown placeholder {exc} in naming template {template!r}"
            ) from exc


class RoutingEngine:
    """
    Copies or moves completed bounce output files to their final destinations.

    The routing pipeline is:
    1. Optionally rename the file using :class:`NamingEngine`.
    2. Copy to ``job.copy_dest`` if set.
    """

    def route(
        self,
        source: Path,
        job: BounceJob,
        batch_index: int = 0,
        rename: bool = True,
        move: bool = False,
    ) -> Path:
        """
        Route *source* file according to the job's configuration.

        Parameters
        ----------
        source:
            Path to the raw bounce output file.
        job:
            The bounce job that produced *source*.
        batch_index:
            Position in the queue (used for ``{index}`` template token).
        rename:
            If *True* the output file is renamed via the naming template.
        move:
            If *True* the source file is moved instead of copied.

        Returns
        -------
        Path
            Final path of the (possibly renamed, possibly copied) file.
        """
        dest_dir = job.copy_dest or source.parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        if rename:
            engine = NamingEngine(job, batch_index=batch_index)
            stem = engine.resolve()
            final_name = stem + source.suffix
        else:
            final_name = source.name

        final_path = dest_dir / final_name

        if source == final_path:
            logger.debug("RoutingEngine: source == dest, skipping copy")
            return final_path

        if move:
            shutil.move(str(source), str(final_path))
            logger.info("RoutingEngine: moved %s → %s", source, final_path)
        else:
            shutil.copy2(str(source), str(final_path))
            logger.info("RoutingEngine: copied %s → %s", source, final_path)

        return final_path

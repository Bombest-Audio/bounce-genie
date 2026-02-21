"""Naming & routing – build output filenames and copy files to destinations."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from string import Template

from bounce_genie.models import BounceJob

logger = logging.getLogger(__name__)


class NamingError(ValueError):
    """Raised when a naming template cannot be rendered."""


def render_name(template: str, job: BounceJob, index: int = 0) -> str:
    """Render *template* for *job*, returning the desired base filename.

    Template variables (Python :class:`string.Template` syntax, i.e. ``$var``
    or ``${var}``):

    ``$session_name``
        Stem of the session file (no extension).
    ``$index``
        Zero-based position of this job in the batch (padded to 3 digits).
    ``$index1``
        One-based position (padded to 3 digits).
    ``$session_ext``
        Extension of the session file including the dot, e.g. ``.ptx``.

    Parameters
    ----------
    template:
        A :class:`string.Template`-style format string, e.g.
        ``"${session_name}_bounce"``.
    job:
        The :class:`~bounce_genie.models.BounceJob` for which the name is
        being rendered.
    index:
        Zero-based position in the current batch.

    Returns
    -------
    str
        The rendered filename stem (no extension).
    """
    session_path = job.session_path
    mapping = {
        "session_name": session_path.stem,
        "session_ext": session_path.suffix,
        "index": str(index).zfill(3),
        "index1": str(index + 1).zfill(3),
    }
    try:
        return Template(template).substitute(mapping)
    except (KeyError, ValueError) as exc:
        raise NamingError(
            f"Invalid naming template {template!r}: {exc}"
        ) from exc


def apply_routing(
    output_files: list[Path],
    job: BounceJob,
    rendered_name: str,
) -> list[Path]:
    """Rename and/or copy *output_files* according to *job* settings.

    If ``job.copy_dest`` is set the files are **copied** (not moved) to that
    directory with the rendered name applied.  Otherwise the files are
    renamed in-place.

    Parameters
    ----------
    output_files:
        The raw output files produced by the bounce.
    job:
        The originating job (provides ``copy_dest``).
    rendered_name:
        The base filename (stem) to apply.

    Returns
    -------
    list[Path]
        Final paths of all processed output files.
    """
    final_paths: list[Path] = []

    for i, src in enumerate(output_files):
        suffix = src.suffix
        # Disambiguate multiple outputs by appending an index
        if len(output_files) > 1:
            dest_name = f"{rendered_name}_{i + 1}{suffix}"
        else:
            dest_name = f"{rendered_name}{suffix}"

        if job.copy_dest is not None:
            dest_dir = Path(job.copy_dest)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / dest_name
            shutil.copy2(src, dest)
            logger.info("Copied %s → %s", src, dest)
        else:
            dest = src.with_name(dest_name)
            src.rename(dest)
            logger.info("Renamed %s → %s", src, dest)

        final_paths.append(dest)

    return final_paths

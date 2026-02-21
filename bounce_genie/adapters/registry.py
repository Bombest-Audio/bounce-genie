"""
bounce_genie.adapters.registry – adapter auto-detection helper.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..models import BounceJob, DawType
from .base import IDawAdapter
from .protools import ProToolsAdapter
from .logic import LogicAdapter
from .cubase import CubaseAdapter
from .ableton import AbletonAdapter

_EXTENSION_MAP: dict[str, type[IDawAdapter]] = {
    ext: adapter_cls
    for adapter_cls in (ProToolsAdapter, LogicAdapter, CubaseAdapter, AbletonAdapter)
    for ext in adapter_cls.SESSION_EXTENSIONS
}

_DAW_TYPE_MAP: dict[DawType, type[IDawAdapter]] = {
    DawType.PRO_TOOLS: ProToolsAdapter,
    DawType.LOGIC_PRO: LogicAdapter,
    DawType.CUBASE: CubaseAdapter,
    DawType.ABLETON_LIVE: AbletonAdapter,
}


def get_adapter_for_job(job: BounceJob, automation_engine=None) -> IDawAdapter:
    """
    Return the correct :class:`IDawAdapter` instance for *job*.

    Resolution order:
    1. ``job.options.daw_type`` if explicitly set.
    2. Session file extension.

    Raises
    ------
    ValueError
        If no adapter can be determined for the job.
    """
    adapter_cls: Optional[type[IDawAdapter]] = None

    if job.options.daw_type is not None:
        adapter_cls = _DAW_TYPE_MAP.get(job.options.daw_type)
        if adapter_cls is None:
            raise ValueError(f"No adapter registered for DawType {job.options.daw_type!r}")
    else:
        ext = job.session_path.suffix.lower()
        adapter_cls = _EXTENSION_MAP.get(ext)
        if adapter_cls is None:
            raise ValueError(
                f"Cannot determine DAW adapter for extension {ext!r}. "
                "Set job.options.daw_type explicitly."
            )

    return adapter_cls(automation_engine=automation_engine)

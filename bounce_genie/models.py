"""
bounce_genie – core data models.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional


class SelectionStrategy(Enum):
    """How the DAW adapter should determine what audio range to bounce."""

    USE_SAVED_SELECTION = auto()  # default – use whatever the session saved
    SELECT_ALL = auto()           # fall back to select-all (e.g. Pro Tools)
    TRIMMED_COPY = auto()         # open a trimmed project copy (Logic/Cubase/Ableton)


class AudioFormat(Enum):
    """Output audio formats that can be requested per bounce job."""

    WAV = "wav"
    AIFF = "aiff"
    MP3 = "mp3"
    AAC = "aac"
    FLAC = "flac"


class DawType(Enum):
    """Supported DAW identifiers."""

    PRO_TOOLS = "protools"
    LOGIC_PRO = "logic"
    CUBASE = "cubase"
    ABLETON_LIVE = "ableton"


class JobStatus(Enum):
    """Lifecycle states for a single bounce job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BounceOptions:
    """Per-job bounce configuration."""

    formats: List[AudioFormat] = field(default_factory=lambda: [AudioFormat.WAV])
    offline: bool = True          # offline (faster-than-real-time) where supported
    selection_strategy: SelectionStrategy = SelectionStrategy.USE_SAVED_SELECTION
    daw_type: Optional[DawType] = None   # None → auto-detect from session extension


@dataclass
class NotificationTarget:
    """Who/where to notify when a job (or the whole batch) finishes."""

    email: Optional[str] = None
    phone_number: Optional[str] = None   # E.164 format, e.g. "+15551234567"


@dataclass
class BounceJob:
    """Represents a single session-to-audio bounce task."""

    session_path: Path
    naming_template: str = "{session_name}"
    copy_dest: Optional[Path] = None
    notification_target: Optional[NotificationTarget] = None
    options: BounceOptions = field(default_factory=BounceOptions)

    # Runtime state (mutated by the orchestrator)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    output_files: List[Path] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self) -> None:
        self.session_path = Path(self.session_path)
        if self.copy_dest is not None:
            self.copy_dest = Path(self.copy_dest)

    @property
    def session_name(self) -> str:
        """Stem of the session file, used as the default output name."""
        return self.session_path.stem

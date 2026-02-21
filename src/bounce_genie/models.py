"""Core data models for Bounce Genie."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class SelectionStrategy(Enum):
    """How the region to bounce is chosen within each DAW session."""

    USE_SAVED_SELECTION = auto()  # use the selection/range already saved in the session
    SELECT_ALL = auto()           # select everything (fallback)
    TRIMMED_COPY = auto()         # save a trimmed copy of the session first


class BounceFormat(Enum):
    """Audio export formats."""

    WAV = "wav"
    AIFF = "aiff"
    MP3 = "mp3"
    FLAC = "flac"


@dataclass
class BounceOptions:
    """Format and quality settings for a bounce operation."""

    formats: list[BounceFormat] = field(default_factory=lambda: [BounceFormat.WAV])
    offline: bool = True          # True = faster-than-real-time offline bounce
    sample_rate: int = 44100
    bit_depth: int = 24
    selection_strategy: SelectionStrategy = SelectionStrategy.USE_SAVED_SELECTION


@dataclass
class NotificationTarget:
    """Where to send completion notifications."""

    email: Optional[str] = None
    phone: Optional[str] = None   # E.164 format for SMS, e.g. "+15551234567"


@dataclass
class BounceJob:
    """A single unit of work: one session file to bounce."""

    session_path: Path
    naming_template: str = "${session_name}"
    copy_dest: Optional[Path] = None
    notification_target: Optional[NotificationTarget] = None
    options: BounceOptions = field(default_factory=BounceOptions)

    def __post_init__(self) -> None:
        self.session_path = Path(self.session_path)
        if self.copy_dest is not None:
            self.copy_dest = Path(self.copy_dest)

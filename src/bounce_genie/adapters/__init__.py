"""DAW adapter package."""

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.adapters.protools import ProToolsAdapter
from bounce_genie.adapters.logic import LogicAdapter
from bounce_genie.adapters.cubase import CubaseAdapter
from bounce_genie.adapters.ableton import AbletonAdapter

__all__ = [
    "IDawAdapter",
    "ProToolsAdapter",
    "LogicAdapter",
    "CubaseAdapter",
    "AbletonAdapter",
]

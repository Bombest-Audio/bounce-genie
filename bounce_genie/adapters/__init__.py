"""
bounce_genie.adapters – DAW adapter package.
"""
from .base import IDawAdapter
from .protools import ProToolsAdapter
from .logic import LogicAdapter
from .cubase import CubaseAdapter
from .ableton import AbletonAdapter
from .registry import get_adapter_for_job

__all__ = [
    "IDawAdapter",
    "ProToolsAdapter",
    "LogicAdapter",
    "CubaseAdapter",
    "AbletonAdapter",
    "get_adapter_for_job",
]

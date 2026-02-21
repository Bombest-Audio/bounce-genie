"""Tests for core data models."""

import pytest
from pathlib import Path

from bounce_genie.models import (
    BounceFormat,
    BounceJob,
    BounceOptions,
    NotificationTarget,
    SelectionStrategy,
)


def test_bounce_job_coerces_paths():
    job = BounceJob(session_path="~/sessions/song.ptx")
    assert isinstance(job.session_path, Path)


def test_bounce_job_coerces_copy_dest():
    job = BounceJob(session_path="/tmp/song.ptx", copy_dest="/tmp/out")
    assert isinstance(job.copy_dest, Path)


def test_bounce_job_copy_dest_none():
    job = BounceJob(session_path="/tmp/song.ptx")
    assert job.copy_dest is None


def test_bounce_options_defaults():
    opts = BounceOptions()
    assert opts.formats == [BounceFormat.WAV]
    assert opts.offline is True
    assert opts.selection_strategy == SelectionStrategy.USE_SAVED_SELECTION


def test_selection_strategy_values():
    strategies = list(SelectionStrategy)
    assert SelectionStrategy.USE_SAVED_SELECTION in strategies
    assert SelectionStrategy.SELECT_ALL in strategies
    assert SelectionStrategy.TRIMMED_COPY in strategies


def test_notification_target_optional_fields():
    nt = NotificationTarget()
    assert nt.email is None
    assert nt.phone is None

    nt2 = NotificationTarget(email="a@b.com", phone="+15551234567")
    assert nt2.email == "a@b.com"
    assert nt2.phone == "+15551234567"

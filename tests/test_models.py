"""Tests for bounce_genie.models."""
from pathlib import Path

import pytest

from bounce_genie.models import (
    AudioFormat,
    BounceJob,
    BounceOptions,
    DawType,
    JobStatus,
    NotificationTarget,
    SelectionStrategy,
)


class TestSelectionStrategy:
    def test_enum_members(self):
        assert SelectionStrategy.USE_SAVED_SELECTION
        assert SelectionStrategy.SELECT_ALL
        assert SelectionStrategy.TRIMMED_COPY

    def test_unique_values(self):
        values = [s.value for s in SelectionStrategy]
        assert len(values) == len(set(values))


class TestAudioFormat:
    def test_wav_value(self):
        assert AudioFormat.WAV.value == "wav"

    def test_mp3_value(self):
        assert AudioFormat.MP3.value == "mp3"

    def test_all_formats(self):
        expected = {"wav", "aiff", "mp3", "aac", "flac"}
        actual = {f.value for f in AudioFormat}
        assert actual == expected


class TestDawType:
    def test_protools_value(self):
        assert DawType.PRO_TOOLS.value == "protools"

    def test_all_daws(self):
        expected = {"protools", "logic", "cubase", "ableton"}
        actual = {d.value for d in DawType}
        assert actual == expected


class TestBounceOptions:
    def test_defaults(self):
        opts = BounceOptions()
        assert opts.formats == [AudioFormat.WAV]
        assert opts.offline is True
        assert opts.selection_strategy == SelectionStrategy.USE_SAVED_SELECTION
        assert opts.daw_type is None

    def test_custom_formats(self):
        opts = BounceOptions(formats=[AudioFormat.WAV, AudioFormat.MP3])
        assert AudioFormat.MP3 in opts.formats

    def test_offline_false(self):
        opts = BounceOptions(offline=False)
        assert opts.offline is False


class TestNotificationTarget:
    def test_email_only(self):
        t = NotificationTarget(email="a@b.com")
        assert t.email == "a@b.com"
        assert t.phone_number is None

    def test_phone_only(self):
        t = NotificationTarget(phone_number="+15551234567")
        assert t.phone_number == "+15551234567"
        assert t.email is None


class TestBounceJob:
    def test_defaults(self):
        job = BounceJob(session_path="/path/to/my_song.ptx")
        assert job.status == JobStatus.PENDING
        assert job.naming_template == "{session_name}"
        assert job.copy_dest is None
        assert job.notification_target is None
        assert job.output_files == []
        assert job.error is None

    def test_session_name(self):
        job = BounceJob(session_path="/path/to/my_song.ptx")
        assert job.session_name == "my_song"

    def test_path_coercion(self):
        job = BounceJob(session_path="/path/to/my_song.ptx")
        assert isinstance(job.session_path, Path)

    def test_copy_dest_coercion(self):
        job = BounceJob(
            session_path="/path/to/my_song.ptx",
            copy_dest="/tmp/bounces",
        )
        assert isinstance(job.copy_dest, Path)

    def test_unique_ids(self):
        j1 = BounceJob(session_path="a.ptx")
        j2 = BounceJob(session_path="b.ptx")
        assert j1.id != j2.id

    def test_custom_options(self):
        opts = BounceOptions(formats=[AudioFormat.MP3], offline=False)
        job = BounceJob(session_path="song.ptx", options=opts)
        assert AudioFormat.MP3 in job.options.formats

"""Tests for bounce_genie.detector."""
import time
from pathlib import Path

import pytest

from bounce_genie.detector import BounceOutputDetector, _AUDIO_EXTENSIONS


class TestBounceOutputDetector:
    def test_start_creates_watch_dir(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        detector = BounceOutputDetector(watch_dir)
        detector.start()
        detector.stop()
        assert watch_dir.exists()

    def test_no_new_files_returns_empty(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        watch_dir.mkdir()
        (watch_dir / "old.wav").write_bytes(b"RIFF")  # pre-existing file

        detector = BounceOutputDetector(watch_dir)
        detector.start()
        # Don't add any new files – wait with a short timeout
        new_files = detector.wait_for_new_files(timeout=0.2, poll_interval=0.05)
        detector.stop()
        assert new_files == []

    def test_detects_new_audio_file(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        watch_dir.mkdir()

        detector = BounceOutputDetector(watch_dir)
        detector.start()

        # Simulate a bounce output appearing
        new_wav = watch_dir / "song.wav"
        new_wav.write_bytes(b"RIFF")

        new_files = detector.wait_for_new_files(timeout=5.0, poll_interval=0.05)
        detector.stop()
        assert new_wav in new_files

    def test_ignores_non_audio_files(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        watch_dir.mkdir()

        detector = BounceOutputDetector(watch_dir)
        detector.start()

        (watch_dir / "session.ptx").write_bytes(b"PTX")
        (watch_dir / "readme.txt").write_text("hello")

        new_files = detector.wait_for_new_files(timeout=0.2, poll_interval=0.05)
        detector.stop()
        assert new_files == []

    def test_get_new_files_nonblocking(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        watch_dir.mkdir()

        detector = BounceOutputDetector(watch_dir)
        detector.start()
        # No files created
        assert detector.get_new_files() == []
        detector.stop()

    def test_audio_extensions_set(self):
        assert ".wav" in _AUDIO_EXTENSIONS
        assert ".mp3" in _AUDIO_EXTENSIONS
        assert ".aiff" in _AUDIO_EXTENSIONS
        assert ".flac" in _AUDIO_EXTENSIONS

    def test_baseline_excludes_pre_existing(self, tmp_path):
        watch_dir = tmp_path / "bounces"
        watch_dir.mkdir()
        pre_existing = watch_dir / "old.wav"
        pre_existing.write_bytes(b"RIFF")

        detector = BounceOutputDetector(watch_dir)
        detector.start()

        # Add a genuinely new file
        new_file = watch_dir / "new.wav"
        new_file.write_bytes(b"RIFF")

        new_files = detector.wait_for_new_files(timeout=5.0, poll_interval=0.05)
        detector.stop()

        assert new_file in new_files
        assert pre_existing not in new_files

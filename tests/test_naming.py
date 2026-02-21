"""Tests for bounce_genie.naming."""
from datetime import datetime
from pathlib import Path

import pytest

from bounce_genie.models import AudioFormat, BounceJob, BounceOptions
from bounce_genie.naming import NamingEngine, RoutingEngine


def _job(name: str = "my_song", template: str = "{session_name}", copy_dest=None):
    return BounceJob(
        session_path=f"/sessions/{name}.ptx",
        naming_template=template,
        copy_dest=copy_dest,
    )


_FIXED_DT = datetime(2025, 6, 15, 10, 30, 0)


class TestNamingEngine:
    def test_session_name_only(self):
        engine = NamingEngine(_job(), now=_FIXED_DT)
        assert engine.resolve() == "my_song"

    def test_session_name_placeholder(self):
        engine = NamingEngine(_job(template="{session_name}_bounce"), now=_FIXED_DT)
        assert engine.resolve() == "my_song_bounce"

    def test_format_placeholder(self):
        engine = NamingEngine(
            _job(template="{session_name}_{format}"),
            fmt=AudioFormat.MP3,
            now=_FIXED_DT,
        )
        assert engine.resolve() == "my_song_mp3"

    def test_index_placeholder(self):
        engine = NamingEngine(
            _job(template="{index:02d}_{session_name}"),
            batch_index=3,
            now=_FIXED_DT,
        )
        assert engine.resolve() == "03_my_song"

    def test_date_placeholder(self):
        engine = NamingEngine(_job(template="{date}_{session_name}"), now=_FIXED_DT)
        assert engine.resolve() == "2025-06-15_my_song"

    def test_time_placeholder(self):
        engine = NamingEngine(_job(template="{session_name}_{time}"), now=_FIXED_DT)
        assert engine.resolve() == "my_song_103000"

    def test_unknown_placeholder_raises(self):
        engine = NamingEngine(_job(template="{unknown_key}"), now=_FIXED_DT)
        with pytest.raises(ValueError, match="Unknown placeholder"):
            engine.resolve()


class TestRoutingEngine:
    def test_copy_to_dest(self, tmp_path):
        src = tmp_path / "raw" / "my_song.wav"
        src.parent.mkdir()
        src.write_bytes(b"RIFF")

        dest_dir = tmp_path / "output"
        job = _job(copy_dest=str(dest_dir))
        router = RoutingEngine()
        result = router.route(src, job, rename=False)

        assert result.parent == dest_dir
        assert result.name == "my_song.wav"
        assert result.exists()

    def test_rename_with_template(self, tmp_path):
        src = tmp_path / "my_song.wav"
        src.write_bytes(b"RIFF")

        dest_dir = tmp_path / "output"
        job = BounceJob(
            session_path="/sessions/track.ptx",
            naming_template="{session_name}_final",
            copy_dest=str(dest_dir),
        )
        router = RoutingEngine()
        result = router.route(src, job)

        assert result.stem == "track_final"
        assert result.suffix == ".wav"
        assert result.exists()

    def test_same_source_and_dest_skips_copy(self, tmp_path):
        src = tmp_path / "my_song.wav"
        src.write_bytes(b"RIFF")

        job = BounceJob(
            session_path=str(tmp_path / "my_song.ptx"),
            naming_template="{session_name}",
        )
        router = RoutingEngine()
        result = router.route(src, job)
        # Source equals dest: no copy needed, file still exists
        assert result == src
        assert result.exists()

    def test_move_instead_of_copy(self, tmp_path):
        src = tmp_path / "raw" / "my_song.wav"
        src.parent.mkdir()
        src.write_bytes(b"RIFF")

        dest_dir = tmp_path / "output"
        job = _job(copy_dest=str(dest_dir))
        router = RoutingEngine()
        result = router.route(src, job, rename=False, move=True)

        assert result.exists()
        assert not src.exists()

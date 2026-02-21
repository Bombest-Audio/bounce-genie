"""Tests for naming & routing."""

import shutil
import tempfile
from pathlib import Path

import pytest

from bounce_genie.models import BounceJob
from bounce_genie.naming import NamingError, apply_routing, render_name


def _job(name: str = "my_session", template: str = "${session_name}", copy_dest=None):
    return BounceJob(
        session_path=f"/sessions/{name}.ptx",
        naming_template=template,
        copy_dest=copy_dest,
    )


# ---------- render_name ----------

def test_render_name_session_name():
    job = _job("cool_track")
    assert render_name("${session_name}", job) == "cool_track"


def test_render_name_index():
    job = _job()
    assert render_name("${session_name}_${index1}", job, index=0) == "my_session_001"
    assert render_name("${session_name}_${index1}", job, index=9) == "my_session_010"


def test_render_name_ext():
    job = _job()
    assert render_name("${session_name}${session_ext}", job) == "my_session.ptx"


def test_render_name_bad_template():
    job = _job()
    with pytest.raises(NamingError):
        render_name("${unknown_var}", job)


# ---------- apply_routing ----------

def test_apply_routing_rename_in_place(tmp_path):
    src = tmp_path / "raw_output.wav"
    src.touch()
    job = BounceJob(session_path=tmp_path / "session.ptx")
    final = apply_routing([src], job, "my_bounce")
    assert len(final) == 1
    assert final[0].name == "my_bounce.wav"
    assert final[0].exists()


def test_apply_routing_copy_dest(tmp_path):
    src = tmp_path / "raw.wav"
    src.write_bytes(b"RIFF")
    dest_dir = tmp_path / "dropbox"
    job = BounceJob(session_path=tmp_path / "session.ptx", copy_dest=dest_dir)
    final = apply_routing([src], job, "finished")
    assert final[0] == dest_dir / "finished.wav"
    assert final[0].read_bytes() == b"RIFF"
    # original should still exist
    assert src.exists()


def test_apply_routing_multiple_outputs(tmp_path):
    src_wav = tmp_path / "out.wav"
    src_mp3 = tmp_path / "out.mp3"
    src_wav.touch()
    src_mp3.touch()
    job = BounceJob(session_path=tmp_path / "session.ptx")
    final = apply_routing([src_wav, src_mp3], job, "track")
    names = {f.name for f in final}
    assert "track_1.wav" in names
    assert "track_2.mp3" in names

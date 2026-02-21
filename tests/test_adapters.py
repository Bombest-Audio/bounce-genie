"""Tests for bounce_genie.adapters."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bounce_genie.adapters import (
    AbletonAdapter,
    CubaseAdapter,
    IDawAdapter,
    LogicAdapter,
    ProToolsAdapter,
    get_adapter_for_job,
)
from bounce_genie.adapters.registry import _EXTENSION_MAP
from bounce_genie.models import (
    AudioFormat,
    BounceJob,
    BounceOptions,
    DawType,
    SelectionStrategy,
)


# ── IDawAdapter interface ─────────────────────────────────────────────

class TestIDawAdapterInterface:
    """Ensure IDawAdapter cannot be instantiated directly."""

    def test_is_abstract(self):
        with pytest.raises(TypeError):
            IDawAdapter()  # type: ignore[abstract]

    def test_can_handle_extension(self):
        adapter = ProToolsAdapter()
        assert adapter.can_handle(Path("song.ptx"))
        assert not adapter.can_handle(Path("song.logicx"))


# ── ProToolsAdapter ───────────────────────────────────────────────────

class TestProToolsAdapter:
    def test_session_extensions(self):
        assert ".ptx" in ProToolsAdapter.SESSION_EXTENSIONS
        assert ".pts" in ProToolsAdapter.SESSION_EXTENSIONS

    def test_open_session_missing_file(self):
        adapter = ProToolsAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.open_session(Path("/nonexistent/session.ptx"))

    def test_open_session_calls_engine(self, tmp_path):
        session = tmp_path / "song.ptx"
        session.touch()
        engine = MagicMock()
        adapter = ProToolsAdapter(automation_engine=engine)
        adapter.open_session(session)
        engine.open_application.assert_called_once_with("Pro Tools")
        engine.open_file.assert_called_once_with(session)

    def test_prep_bounce_select_all_shortcut(self):
        engine = MagicMock()
        adapter = ProToolsAdapter(automation_engine=engine)
        opts = BounceOptions()
        adapter.prep_bounce(SelectionStrategy.SELECT_ALL, opts)
        engine.send_shortcut.assert_called_once_with("cmd+a")
        engine.open_menu.assert_called()

    def test_prep_bounce_use_saved_selection_no_shortcut(self):
        engine = MagicMock()
        adapter = ProToolsAdapter(automation_engine=engine)
        opts = BounceOptions()
        adapter.prep_bounce(SelectionStrategy.USE_SAVED_SELECTION, opts)
        engine.send_shortcut.assert_not_called()

    def test_execute_bounce_clicks_button(self):
        engine = MagicMock()
        adapter = ProToolsAdapter(automation_engine=engine)
        adapter.execute_bounce(BounceOptions())
        engine.click_button.assert_called_once_with("Bounce")

    def test_detect_outputs_missing_dir(self, tmp_path):
        job = BounceJob(session_path=tmp_path / "song.ptx")
        adapter = ProToolsAdapter()
        assert adapter.detect_outputs(job) == []

    def test_detect_outputs_finds_files(self, tmp_path):
        bounce_dir = tmp_path / "Bounced Files"
        bounce_dir.mkdir()
        (bounce_dir / "song.wav").write_bytes(b"RIFF")
        (bounce_dir / "song.mp3").write_bytes(b"ID3")
        job = BounceJob(session_path=tmp_path / "song.ptx")
        adapter = ProToolsAdapter()
        files = adapter.detect_outputs(job)
        assert len(files) == 2


# ── LogicAdapter ──────────────────────────────────────────────────────

class TestLogicAdapter:
    def test_session_extensions(self):
        assert ".logicx" in LogicAdapter.SESSION_EXTENSIONS

    def test_open_session_missing_file(self):
        adapter = LogicAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.open_session(Path("/nonexistent/session.logicx"))

    def test_prep_bounce_trimmed_copy(self):
        engine = MagicMock()
        adapter = LogicAdapter(automation_engine=engine)
        adapter.prep_bounce(SelectionStrategy.TRIMMED_COPY, BounceOptions())
        engine.open_menu.assert_any_call("File", "Save As…")

    def test_detect_outputs_finds_files(self, tmp_path):
        bounces_dir = tmp_path / "Bounces"
        bounces_dir.mkdir()
        (bounces_dir / "mix.aiff").write_bytes(b"FORM")
        job = BounceJob(session_path=tmp_path / "project.logicx")
        adapter = LogicAdapter()
        files = adapter.detect_outputs(job)
        assert len(files) == 1


# ── CubaseAdapter ─────────────────────────────────────────────────────

class TestCubaseAdapter:
    def test_session_extensions(self):
        assert ".cpr" in CubaseAdapter.SESSION_EXTENSIONS

    def test_open_session_missing_file(self):
        adapter = CubaseAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.open_session(Path("/nonexistent/session.cpr"))

    def test_execute_bounce_clicks_export(self):
        engine = MagicMock()
        adapter = CubaseAdapter(automation_engine=engine)
        adapter.execute_bounce(BounceOptions())
        engine.click_button.assert_called_once_with("Export")


# ── AbletonAdapter ────────────────────────────────────────────────────

class TestAbletonAdapter:
    def test_session_extensions(self):
        assert ".als" in AbletonAdapter.SESSION_EXTENSIONS

    def test_open_session_missing_file(self):
        adapter = AbletonAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.open_session(Path("/nonexistent/session.als"))

    def test_detect_outputs_filters_audio(self, tmp_path):
        (tmp_path / "bounce.wav").write_bytes(b"RIFF")
        (tmp_path / "session.als").write_bytes(b"")
        (tmp_path / "readme.txt").write_text("hello")
        job = BounceJob(session_path=tmp_path / "session.als")
        adapter = AbletonAdapter()
        files = adapter.detect_outputs(job)
        assert all(f.suffix.lower() == ".wav" for f in files)
        assert len(files) == 1


# ── Registry / get_adapter_for_job ───────────────────────────────────

class TestRegistry:
    def test_auto_detect_ptx(self):
        job = BounceJob(session_path="/sessions/song.ptx")
        adapter = get_adapter_for_job(job)
        assert isinstance(adapter, ProToolsAdapter)

    def test_auto_detect_logicx(self):
        job = BounceJob(session_path="/sessions/song.logicx")
        adapter = get_adapter_for_job(job)
        assert isinstance(adapter, LogicAdapter)

    def test_auto_detect_cpr(self):
        job = BounceJob(session_path="/sessions/song.cpr")
        adapter = get_adapter_for_job(job)
        assert isinstance(adapter, CubaseAdapter)

    def test_auto_detect_als(self):
        job = BounceJob(session_path="/sessions/song.als")
        adapter = get_adapter_for_job(job)
        assert isinstance(adapter, AbletonAdapter)

    def test_explicit_daw_type_overrides_extension(self):
        opts = BounceOptions(daw_type=DawType.LOGIC_PRO)
        job = BounceJob(session_path="/sessions/song.ptx", options=opts)
        adapter = get_adapter_for_job(job)
        assert isinstance(adapter, LogicAdapter)

    def test_unknown_extension_raises(self):
        job = BounceJob(session_path="/sessions/song.unknown")
        with pytest.raises(ValueError, match="Cannot determine"):
            get_adapter_for_job(job)

    def test_extension_map_completeness(self):
        all_extensions = set()
        for cls in (ProToolsAdapter, LogicAdapter, CubaseAdapter, AbletonAdapter):
            all_extensions.update(cls.SESSION_EXTENSIONS)
        assert set(_EXTENSION_MAP.keys()) == all_extensions

"""Tests for bounce_genie.orchestrator."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.automation.engine import AutomationEngine
from bounce_genie.models import (
    BounceJob,
    BounceOptions,
    JobStatus,
    NotificationTarget,
    SelectionStrategy,
)
from bounce_genie.notifications.manager import NotificationManager
from bounce_genie.orchestrator import BounceOrchestrator
from bounce_genie.queue import BounceQueue


def _make_queue(*session_paths: str) -> BounceQueue:
    q = BounceQueue()
    for path in session_paths:
        q.add(BounceJob(session_path=path))
    return q


def _make_mock_adapter(output_files=None) -> MagicMock:
    adapter = MagicMock(spec=IDawAdapter)
    adapter.detect_outputs.return_value = output_files or []
    return adapter


class TestBounceOrchestrator:
    def test_processes_all_jobs(self, tmp_path):
        session = tmp_path / "song.ptx"
        session.touch()
        q = _make_queue(str(session))

        mock_adapter = _make_mock_adapter()
        engine = AutomationEngine(dry_run=True)
        notifier = MagicMock(spec=NotificationManager)

        with patch(
            "bounce_genie.orchestrator.get_adapter_for_job",
            return_value=mock_adapter,
        ):
            orch = BounceOrchestrator(
                queue=q,
                automation_engine=engine,
                notification_manager=notifier,
                bounce_timeout=0.1,
            )
            orch.run()

        assert q.is_finished()
        jobs = q.all_jobs
        assert len(jobs) == 1
        assert jobs[0].status == JobStatus.COMPLETED

    def test_marks_failed_on_file_not_found(self):
        q = _make_queue("/nonexistent/session.ptx")
        engine = AutomationEngine(dry_run=True)
        notifier = MagicMock(spec=NotificationManager)

        orch = BounceOrchestrator(
            queue=q,
            automation_engine=engine,
            notification_manager=notifier,
        )
        orch.run()

        assert q.all_jobs[0].status == JobStatus.FAILED

    def test_calls_notification_manager(self, tmp_path):
        session = tmp_path / "song.ptx"
        session.touch()
        q = _make_queue(str(session))

        mock_adapter = _make_mock_adapter()
        engine = AutomationEngine(dry_run=True)
        notifier = MagicMock(spec=NotificationManager)

        with patch(
            "bounce_genie.orchestrator.get_adapter_for_job",
            return_value=mock_adapter,
        ):
            orch = BounceOrchestrator(
                queue=q,
                automation_engine=engine,
                notification_manager=notifier,
                bounce_timeout=0.1,
            )
            orch.run()

        notifier.send_job_complete.assert_called_once()
        notifier.send_batch_summary.assert_called_once()

    def test_multiple_jobs_processed_in_order(self, tmp_path):
        sessions = []
        for i in range(3):
            s = tmp_path / f"song{i}.ptx"
            s.touch()
            sessions.append(str(s))

        q = _make_queue(*sessions)
        engine = AutomationEngine(dry_run=True)
        notifier = MagicMock(spec=NotificationManager)
        mock_adapter = _make_mock_adapter()

        with patch(
            "bounce_genie.orchestrator.get_adapter_for_job",
            return_value=mock_adapter,
        ):
            orch = BounceOrchestrator(
                queue=q,
                automation_engine=engine,
                notification_manager=notifier,
                bounce_timeout=0.1,
            )
            orch.run()

        completed = [j for j in q.all_jobs if j.status == JobStatus.COMPLETED]
        assert len(completed) == 3

    def test_copy_dest_routes_output(self, tmp_path):
        session = tmp_path / "song.ptx"
        session.touch()

        # Create a fake bounce output
        bounce_dir = tmp_path / "Bounced Files"
        bounce_dir.mkdir()
        output_wav = bounce_dir / "song.wav"
        output_wav.write_bytes(b"RIFF")

        copy_dest = tmp_path / "final"

        job = BounceJob(
            session_path=session,
            copy_dest=copy_dest,
            naming_template="{session_name}",
        )
        q = BounceQueue()
        q.add(job)

        mock_adapter = _make_mock_adapter(output_files=[output_wav])
        engine = AutomationEngine(dry_run=True)
        notifier = MagicMock(spec=NotificationManager)

        with patch(
            "bounce_genie.orchestrator.get_adapter_for_job",
            return_value=mock_adapter,
        ):
            orch = BounceOrchestrator(
                queue=q,
                automation_engine=engine,
                notification_manager=notifier,
                bounce_timeout=0.1,
            )
            orch.run()

        assert job.status == JobStatus.COMPLETED
        assert copy_dest.exists()

    def test_unknown_extension_marks_failed(self):
        q = _make_queue("/sessions/song.xyz")
        # No tmp file, so this hits ValueError from registry before FileNotFoundError
        engine = AutomationEngine(dry_run=True)
        orch = BounceOrchestrator(queue=q, automation_engine=engine, bounce_timeout=0.1)
        orch.run()
        assert q.all_jobs[0].status == JobStatus.FAILED

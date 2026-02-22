"""Tests for the BatchRunner using stubbed adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.models import BounceJob, BounceOptions, SelectionStrategy
from bounce_genie.notifications.base import BaseNotifier, BatchResult
from bounce_genie.queue import JobQueue
from bounce_genie.runner import BatchRunner


# ---------- Test doubles ----------

class _StubAdapter(IDawAdapter):
    """Records calls and returns configurable output files."""

    def __init__(self, outputs: list[Path] | None = None, fail: bool = False) -> None:
        self.calls: list[str] = []
        self._outputs = outputs or []
        self._fail = fail

    def open_session(self, path: Path) -> None:
        self.calls.append("open_session")

    def close_session(self) -> None:
        self.calls.append("close_session")

    def prep_bounce(self, selection_strategy: SelectionStrategy, options: BounceOptions) -> None:
        self.calls.append("prep_bounce")

    def execute_bounce(self, options: BounceOptions) -> None:
        self.calls.append("execute_bounce")
        if self._fail:
            raise RuntimeError("Simulated bounce failure")

    def detect_outputs(self, job: BounceJob) -> list[Path]:
        self.calls.append("detect_outputs")
        return list(self._outputs)


class _CapturingNotifier(BaseNotifier):
    def __init__(self) -> None:
        self.results: list[BatchResult] = []

    def send(self, result: BatchResult, recipient: str) -> None:
        self.results.append(result)


# ---------- Tests ----------

def test_runner_processes_all_jobs(tmp_path):
    # Give each job its own output directory so renames don't collide
    dir1 = tmp_path / "job1"
    dir2 = tmp_path / "job2"
    dir1.mkdir()
    dir2.mkdir()

    wav1 = dir1 / "out1.wav"
    wav2 = dir2 / "out2.wav"
    wav1.touch()
    wav2.touch()

    outputs_by_job = {0: [wav1], 1: [wav2]}
    call_count = {"n": 0}

    class _MultiAdapter(_StubAdapter):
        def detect_outputs(self, job: BounceJob) -> list[Path]:
            self.calls.append("detect_outputs")
            idx = call_count["n"]
            call_count["n"] += 1
            return list(outputs_by_job[idx])

    adapter = _MultiAdapter()
    queue = JobQueue()
    job1 = BounceJob(session_path=dir1 / "s1.ptx")
    job2 = BounceJob(session_path=dir2 / "s2.ptx")
    queue.add_many([job1, job2])

    runner = BatchRunner(adapter=adapter, queue=queue, pause_on_error=False)
    result = runner.run()

    assert result.total == 2
    assert result.succeeded == 2
    assert result.failed == 0


def test_runner_stops_on_error_by_default(tmp_path):
    adapter = _StubAdapter(fail=True)
    queue = JobQueue()
    queue.add_many([
        BounceJob(session_path=tmp_path / "s1.ptx"),
        BounceJob(session_path=tmp_path / "s2.ptx"),
    ])
    runner = BatchRunner(adapter=adapter, queue=queue, pause_on_error=True)
    result = runner.run()

    assert result.failed == 1
    # Second job should remain unprocessed when pause_on_error=True
    assert result.succeeded == 0


def test_runner_continues_on_error_when_configured(tmp_path):
    adapter = _StubAdapter(fail=True)
    queue = JobQueue()
    queue.add_many([
        BounceJob(session_path=tmp_path / "s1.ptx"),
        BounceJob(session_path=tmp_path / "s2.ptx"),
    ])
    runner = BatchRunner(adapter=adapter, queue=queue, pause_on_error=False)
    result = runner.run()

    assert result.failed == 2
    assert result.total == 2


def test_runner_notifies_after_completion(tmp_path):
    notifier = _CapturingNotifier()
    adapter = _StubAdapter()
    queue = JobQueue()
    queue.add(BounceJob(session_path=tmp_path / "s1.ptx"))
    runner = BatchRunner(adapter=adapter, queue=queue, notifiers=[notifier])
    runner.run()

    assert len(notifier.results) == 1


def test_runner_adapter_call_order(tmp_path):
    wav = tmp_path / "out.wav"
    wav.touch()
    adapter = _StubAdapter(outputs=[wav])
    queue = JobQueue()
    queue.add(BounceJob(session_path=tmp_path / "session.ptx"))
    runner = BatchRunner(adapter=adapter, queue=queue)
    runner.run()

    assert adapter.calls == [
        "open_session",
        "prep_bounce",
        "execute_bounce",
        "detect_outputs",
        "close_session",
    ]

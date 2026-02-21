"""Tests for bounce_genie.queue."""
import pytest

from bounce_genie.models import BounceJob, JobStatus
from bounce_genie.queue import BounceQueue


def _make_job(name: str) -> BounceJob:
    return BounceJob(session_path=f"/sessions/{name}.ptx")


class TestBounceQueue:
    def test_initially_empty(self):
        q = BounceQueue()
        assert len(q) == 0
        assert q.pending_count == 0

    def test_add_single_job(self):
        q = BounceQueue()
        job = _make_job("song1")
        q.add(job)
        assert len(q) == 1
        assert q.pending_count == 1

    def test_add_all(self):
        q = BounceQueue()
        jobs = [_make_job(f"song{i}") for i in range(3)]
        q.add_all(jobs)
        assert len(q) == 3
        assert q.pending_count == 3

    def test_next_pending_returns_first(self):
        q = BounceQueue()
        j1 = _make_job("song1")
        j2 = _make_job("song2")
        q.add_all([j1, j2])
        job = q.next_pending()
        assert job is j1
        assert job.status == JobStatus.IN_PROGRESS

    def test_next_pending_when_empty(self):
        q = BounceQueue()
        assert q.next_pending() is None

    def test_next_pending_skips_non_pending(self):
        q = BounceQueue()
        j1 = _make_job("song1")
        j2 = _make_job("song2")
        q.add_all([j1, j2])
        q.next_pending()  # j1 becomes IN_PROGRESS
        job = q.next_pending()  # should return j2
        assert job is j2

    def test_mark_completed(self):
        q = BounceQueue()
        job = _make_job("song1")
        q.add(job)
        q.next_pending()
        q.mark_completed(job)
        assert job.status == JobStatus.COMPLETED
        assert q.completed_jobs == [job]

    def test_mark_failed(self):
        q = BounceQueue()
        job = _make_job("song1")
        q.add(job)
        q.next_pending()
        q.mark_failed(job, "test error")
        assert job.status == JobStatus.FAILED
        assert job.error == "test error"
        assert q.failed_jobs == [job]

    def test_mark_skipped(self):
        q = BounceQueue()
        job = _make_job("song1")
        q.add(job)
        q.next_pending()
        q.mark_skipped(job, "skipped reason")
        assert job.status == JobStatus.SKIPPED
        assert job.error == "skipped reason"

    def test_is_finished_all_done(self):
        q = BounceQueue()
        jobs = [_make_job(f"s{i}") for i in range(2)]
        q.add_all(jobs)
        for job in [q.next_pending(), q.next_pending()]:
            q.mark_completed(job)
        assert q.is_finished()

    def test_is_finished_with_pending(self):
        q = BounceQueue()
        q.add(_make_job("song"))
        assert not q.is_finished()

    def test_all_jobs_returns_copy(self):
        q = BounceQueue()
        q.add(_make_job("song"))
        jobs = q.all_jobs
        assert len(jobs) == 1

    def test_iteration(self):
        q = BounceQueue()
        jobs = [_make_job(f"s{i}") for i in range(3)]
        q.add_all(jobs)
        listed = list(q)
        assert len(listed) == 3

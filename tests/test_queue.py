"""Tests for the JobQueue."""

import pytest
from bounce_genie.models import BounceJob
from bounce_genie.queue import JobQueue


def _make_job(name: str) -> BounceJob:
    return BounceJob(session_path=f"/sessions/{name}.ptx")


def test_add_and_next():
    q = JobQueue()
    job = _make_job("song1")
    q.add(job)
    assert len(q) == 1
    result = q.next()
    assert result is job
    assert len(q) == 0


def test_fifo_order():
    q = JobQueue()
    jobs = [_make_job(f"song{i}") for i in range(3)]
    q.add_many(jobs)
    for expected in jobs:
        assert q.next() is expected


def test_next_empty_returns_none():
    q = JobQueue()
    assert q.next() is None


def test_is_empty():
    q = JobQueue()
    assert q.is_empty()
    q.add(_make_job("x"))
    assert not q.is_empty()


def test_peek_does_not_remove():
    q = JobQueue()
    job = _make_job("peek")
    q.add(job)
    assert q.peek() is job
    assert len(q) == 1


def test_peek_empty_returns_none():
    q = JobQueue()
    assert q.peek() is None


def test_clear():
    q = JobQueue()
    q.add_many([_make_job(f"s{i}") for i in range(5)])
    q.clear()
    assert q.is_empty()
    assert len(q) == 0

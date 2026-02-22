"""Tests for notifications."""

import pytest

from bounce_genie.notifications.base import BatchResult


def test_batch_result_summary_text_no_errors():
    result = BatchResult(total=3, succeeded=3, failed=0)
    summary = result.summary_text()
    assert "3" in summary
    assert "0" in summary or "✗ 0" in summary


def test_batch_result_summary_text_with_errors():
    result = BatchResult(total=2, succeeded=1, failed=1, errors=["song2.ptx: timeout"])
    summary = result.summary_text()
    assert "song2.ptx: timeout" in summary


def test_batch_result_success_rate_zero_total():
    result = BatchResult()
    assert result.success_rate == 0.0


def test_batch_result_success_rate():
    result = BatchResult(total=4, succeeded=3)
    assert result.success_rate == pytest.approx(0.75)


def test_batch_result_outputs_in_summary(tmp_path):
    from pathlib import Path
    p = tmp_path / "song.wav"
    result = BatchResult(total=1, succeeded=1, outputs=[p])
    summary = result.summary_text()
    assert str(p) in summary

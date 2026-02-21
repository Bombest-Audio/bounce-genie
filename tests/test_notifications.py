"""Tests for bounce_genie.notifications."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bounce_genie.models import BounceJob, JobStatus, NotificationTarget
from bounce_genie.notifications.base import BaseNotifier, BatchSummary
from bounce_genie.notifications.email_notifier import EmailNotifier, SmtpConfig
from bounce_genie.notifications.manager import NotificationManager


# ── BatchSummary ──────────────────────────────────────────────────────

class TestBatchSummary:
    def test_as_text_contains_counts(self):
        summary = BatchSummary(total=5, completed=4, failed=1)
        text = summary.as_text()
        assert "5" in text
        assert "4" in text
        assert "1" in text

    def test_as_text_lists_errors(self):
        summary = BatchSummary(total=1, failed=1, errors=["something went wrong"])
        text = summary.as_text()
        assert "something went wrong" in text

    def test_as_text_lists_output_files(self):
        summary = BatchSummary(
            total=1,
            completed=1,
            output_files=[Path("/bounces/song.wav")],
        )
        text = summary.as_text()
        assert "song.wav" in text

    def test_empty_summary(self):
        summary = BatchSummary()
        text = summary.as_text()
        assert "0" in text


# ── EmailNotifier ─────────────────────────────────────────────────────

class TestEmailNotifier:
    def _make_notifier(self):
        config = SmtpConfig(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            use_tls=True,
            sender="genie@example.com",
        )
        return EmailNotifier(config)

    @patch("bounce_genie.notifications.email_notifier.smtplib.SMTP")
    def test_notify_sends_email(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        notifier = self._make_notifier()
        summary = BatchSummary(total=2, completed=2, failed=0)
        notifier.notify(summary, "user@example.com")

        mock_smtp.send_message.assert_called_once()

    @patch("bounce_genie.notifications.email_notifier.smtplib.SMTP")
    def test_notify_job_complete_with_email_target(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        job = BounceJob(
            session_path="/sessions/song.ptx",
            notification_target=NotificationTarget(email="user@example.com"),
        )
        job.output_files = [Path("/bounces/song.wav")]

        notifier = self._make_notifier()
        notifier.notify_job_complete(job)

        mock_smtp.send_message.assert_called_once()

    def test_notify_job_complete_no_target_does_nothing(self):
        job = BounceJob(session_path="/sessions/song.ptx")
        notifier = self._make_notifier()
        # Should not raise
        notifier.notify_job_complete(job)

    @patch("bounce_genie.notifications.email_notifier.smtplib.SMTP")
    def test_smtp_error_propagates(self, mock_smtp_class):
        mock_smtp_class.side_effect = ConnectionRefusedError("refused")
        notifier = self._make_notifier()
        summary = BatchSummary(total=1, completed=1)
        with pytest.raises(ConnectionRefusedError):
            notifier.notify(summary, "user@example.com")


# ── SmsNotifier ───────────────────────────────────────────────────────

class TestSmsNotifier:
    def test_import_error_without_twilio(self):
        import sys
        # Hide twilio from imports
        with patch.dict(sys.modules, {"twilio": None, "twilio.rest": None}):
            from bounce_genie.notifications import sms_notifier
            import importlib
            importlib.reload(sms_notifier)
            from bounce_genie.notifications.sms_notifier import SmsNotifier, TwilioConfig
            config = TwilioConfig(
                account_sid="ACxxx",
                auth_token="token",
                from_number="+15550000000",
            )
            with pytest.raises(ImportError, match="twilio"):
                SmsNotifier(config)


# ── NotificationManager ───────────────────────────────────────────────

class TestNotificationManager:
    def test_register_and_dispatch(self):
        notifier = MagicMock(spec=BaseNotifier)
        manager = NotificationManager([notifier])

        job = BounceJob(session_path="/sessions/song.ptx")
        job.status = JobStatus.COMPLETED

        manager.send_job_complete(job)
        notifier.notify_job_complete.assert_called_once_with(job)

    def test_send_batch_summary_dispatches_to_all(self):
        n1 = MagicMock(spec=BaseNotifier)
        n2 = MagicMock(spec=BaseNotifier)
        manager = NotificationManager([n1, n2])

        job = BounceJob(
            session_path="/s/song.ptx",
            notification_target=NotificationTarget(email="a@b.com"),
        )
        job.status = JobStatus.COMPLETED

        manager.send_batch_summary([job])

        n1.notify.assert_called_once()
        n2.notify.assert_called_once()

    def test_notifier_failure_does_not_raise(self):
        notifier = MagicMock(spec=BaseNotifier)
        notifier.notify_job_complete.side_effect = RuntimeError("network down")
        manager = NotificationManager([notifier])

        job = BounceJob(session_path="/s/song.ptx")
        # Should log the error but not propagate it
        manager.send_job_complete(job)

    def test_empty_manager(self):
        manager = NotificationManager()
        job = BounceJob(session_path="/s/song.ptx")
        # Should be a no-op
        manager.send_job_complete(job)
        manager.send_batch_summary([job])

    def test_batch_summary_counts(self):
        notifier = MagicMock(spec=BaseNotifier)
        manager = NotificationManager([notifier])

        j1 = BounceJob(
            session_path="/s/a.ptx",
            notification_target=NotificationTarget(email="x@y.com"),
        )
        j1.status = JobStatus.COMPLETED
        j2 = BounceJob(
            session_path="/s/b.ptx",
            notification_target=NotificationTarget(email="x@y.com"),
        )
        j2.status = JobStatus.FAILED
        j2.error = "oops"

        manager.send_batch_summary([j1, j2])

        call_args = notifier.notify.call_args
        summary = call_args[0][0]
        assert summary.total == 2
        assert summary.completed == 1
        assert summary.failed == 1
        assert "oops" in summary.errors

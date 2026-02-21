"""
bounce_genie.notifications.email_notifier – SMTP email notifier.
"""
from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional

from ..models import BounceJob
from .base import BaseNotifier, BatchSummary

logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    """SMTP connection settings."""

    host: str = "localhost"
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    sender: str = "bounce-genie@localhost"


class EmailNotifier(BaseNotifier):
    """
    Sends notifications via SMTP email.

    Parameters
    ----------
    smtp_config:
        Connection settings for the outbound SMTP server.
    """

    def __init__(self, smtp_config: SmtpConfig) -> None:
        self._config = smtp_config

    def notify(self, summary: BatchSummary, target: str) -> None:
        """Send the batch *summary* to the email address *target*."""
        subject = (
            f"[Bounce Genie] Batch done – "
            f"{summary.completed}/{summary.total} completed"
        )
        body = summary.as_text()
        self._send(to=target, subject=subject, body=body)

    def notify_job_complete(self, job: BounceJob) -> None:
        """Send a per-job notification if the job has an email target."""
        if job.notification_target is None or not job.notification_target.email:
            return
        subject = f"[Bounce Genie] '{job.session_name}' bounce complete"
        body = (
            f"Session: {job.session_path}\n"
            f"Output files ({len(job.output_files)}):\n"
            + "\n".join(f"  - {f}" for f in job.output_files)
        )
        self._send(
            to=job.notification_target.email,
            subject=subject,
            body=body,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self._config.sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP(self._config.host, self._config.port) as smtp:
                if self._config.use_tls:
                    smtp.starttls()
                if self._config.username and self._config.password:
                    smtp.login(self._config.username, self._config.password)
                smtp.send_message(msg)
                logger.info("Email sent to %s | subject: %s", to, subject)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            raise

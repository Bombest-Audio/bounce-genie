"""
bounce_genie.notifications.sms_notifier – Twilio SMS notifier (optional).

Requires the ``twilio`` extra:  pip install bounce-genie[sms]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..models import BounceJob
from .base import BaseNotifier, BatchSummary

logger = logging.getLogger(__name__)


@dataclass
class TwilioConfig:
    """Twilio account credentials."""

    account_sid: str
    auth_token: str
    from_number: str  # Twilio phone number in E.164 format, e.g. "+15551234567"


class SmsNotifier(BaseNotifier):
    """
    Sends SMS notifications via Twilio.

    Parameters
    ----------
    twilio_config:
        Twilio credentials.

    Notes
    -----
    ``twilio`` must be installed separately (``pip install bounce-genie[sms]``).
    If the package is unavailable, an :class:`ImportError` is raised at
    instantiation time.
    """

    def __init__(self, twilio_config: TwilioConfig) -> None:
        try:
            from twilio.rest import Client  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "The 'twilio' package is required for SMS notifications. "
                "Install it with: pip install bounce-genie[sms]"
            ) from exc

        self._config = twilio_config
        self._client = Client(twilio_config.account_sid, twilio_config.auth_token)

    def notify(self, summary: BatchSummary, target: str) -> None:
        """Send the batch *summary* as an SMS to *target* (E.164 phone number)."""
        body = (
            f"Bounce Genie: batch done. "
            f"{summary.completed}/{summary.total} ok, "
            f"{summary.failed} failed."
        )
        self._send_sms(to=target, body=body)

    def notify_job_complete(self, job: BounceJob) -> None:
        """Send a per-job SMS if the job has a phone number target."""
        if job.notification_target is None or not job.notification_target.phone_number:
            return
        body = f"Bounce Genie: '{job.session_name}' bounce complete ({len(job.output_files)} file(s))."
        self._send_sms(to=job.notification_target.phone_number, body=body)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send_sms(self, to: str, body: str) -> None:
        try:
            message = self._client.messages.create(
                body=body,
                from_=self._config.from_number,
                to=to,
            )
            logger.info("SMS sent to %s | SID: %s", to, message.sid)
        except Exception as exc:
            logger.error("Failed to send SMS to %s: %s", to, exc)
            raise

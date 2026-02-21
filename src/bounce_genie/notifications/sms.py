"""SMS notifier – sends batch results via Twilio."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bounce_genie.notifications.base import BaseNotifier, BatchResult

logger = logging.getLogger(__name__)


@dataclass
class TwilioConfig:
    """Twilio API credentials and sender phone number."""

    account_sid: str
    auth_token: str
    from_number: str  # E.164, e.g. "+15551234567"


class SmsNotifier(BaseNotifier):
    """Sends completion notifications by SMS via the Twilio REST API.

    Parameters
    ----------
    config:
        Twilio credentials and sender number.

    Notes
    -----
    The ``twilio`` package must be installed::

        pip install twilio
    """

    def __init__(self, config: TwilioConfig) -> None:
        self.config = config
        self._client = None  # lazily initialised

    def _get_client(self) -> object:
        if self._client is None:
            try:
                from twilio.rest import Client  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "twilio is not installed. Install it with: pip install twilio"
                ) from exc
            self._client = Client(self.config.account_sid, self.config.auth_token)
        return self._client

    def send(self, result: BatchResult, recipient: str) -> None:
        """Send an SMS summary of *result* to *recipient*.

        Parameters
        ----------
        result:
            The completed batch summary.
        recipient:
            The recipient's phone number in E.164 format (e.g. ``"+15551234567"``).
        """
        body = (
            f"Bounce Genie: {result.succeeded}/{result.total} bounces complete, "
            f"{result.failed} failed."
        )
        logger.info("Sending SMS to %s", recipient)
        client = self._get_client()
        message = client.messages.create(  # type: ignore[attr-defined]
            body=body,
            from_=self.config.from_number,
            to=recipient,
        )
        logger.info("SMS sent (SID: %s)", message.sid)

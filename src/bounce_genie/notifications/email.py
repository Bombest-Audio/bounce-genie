"""Email notifier – sends batch results via SMTP."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from bounce_genie.notifications.base import BaseNotifier, BatchResult

logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    """SMTP connection settings."""

    host: str = "localhost"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_address: str = "bounce-genie@localhost"


class EmailNotifier(BaseNotifier):
    """Sends completion notifications by email using SMTP.

    Parameters
    ----------
    config:
        SMTP server configuration.  Defaults to a plain ``localhost:587``
        connection with no authentication.
    """

    def __init__(self, config: SmtpConfig | None = None) -> None:
        self.config = config or SmtpConfig()

    def send(self, result: BatchResult, recipient: str) -> None:
        """Send an email summary of *result* to *recipient*.

        Parameters
        ----------
        result:
            The completed batch summary.
        recipient:
            The recipient's email address.
        """
        subject = (
            f"Bounce Genie – {result.succeeded}/{result.total} bounces complete"
        )
        body = result.summary_text()

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.config.from_address
        msg["To"] = recipient
        msg.set_content(body)

        logger.info("Sending email to %s via %s:%s", recipient, self.config.host, self.config.port)
        try:
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.username:
                    server.login(self.config.username, self.config.password)
                server.send_message(msg)
            logger.info("Email sent successfully to %s", recipient)
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", recipient, exc)
            raise

"""
bounce_genie.notifications.manager – coordinates multiple notifiers.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ..models import BounceJob
from .base import BaseNotifier, BatchSummary

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Delegates notifications to one or more :class:`BaseNotifier` backends.

    At batch completion, it builds a :class:`BatchSummary` from the job
    queue and dispatches it to all registered notifiers.

    Parameters
    ----------
    notifiers:
        List of notifier backends to dispatch to.
    """

    def __init__(self, notifiers: Optional[List[BaseNotifier]] = None) -> None:
        self._notifiers: List[BaseNotifier] = notifiers or []

    def register(self, notifier: BaseNotifier) -> None:
        """Add *notifier* to the dispatch list."""
        self._notifiers.append(notifier)

    def send_job_complete(self, job: BounceJob) -> None:
        """Notify all backends that *job* has completed (per-job hook)."""
        for notifier in self._notifiers:
            try:
                notifier.notify_job_complete(job)
            except Exception as exc:
                logger.error(
                    "Notifier %s failed for job %s: %s",
                    type(notifier).__name__,
                    job.id,
                    exc,
                )

    def send_batch_summary(
        self,
        jobs: List[BounceJob],
        target_email: Optional[str] = None,
        target_phone: Optional[str] = None,
    ) -> None:
        """
        Build a :class:`BatchSummary` from *jobs* and dispatch to all backends.

        Parameters
        ----------
        jobs:
            All jobs in the completed batch.
        target_email:
            Fallback email address if individual jobs don't specify one.
        target_phone:
            Fallback phone number if individual jobs don't specify one.
        """
        from ..models import JobStatus

        summary = BatchSummary(
            total=len(jobs),
            completed=sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
            failed=sum(1 for j in jobs if j.status == JobStatus.FAILED),
            output_files=[f for j in jobs for f in j.output_files],
            errors=[j.error for j in jobs if j.error],
        )

        # Collect unique notification targets from jobs + fallback params
        emails: set[str] = set()
        phones: set[str] = set()
        for job in jobs:
            if job.notification_target:
                if job.notification_target.email:
                    emails.add(job.notification_target.email)
                if job.notification_target.phone_number:
                    phones.add(job.notification_target.phone_number)
        if target_email:
            emails.add(target_email)
        if target_phone:
            phones.add(target_phone)

        for notifier in self._notifiers:
            notifier_name = type(notifier).__name__
            for email in emails:
                try:
                    notifier.notify(summary, email)
                except Exception as exc:
                    logger.error("%s failed sending to %s: %s", notifier_name, email, exc)
            for phone in phones:
                try:
                    notifier.notify(summary, phone)
                except Exception as exc:
                    logger.error("%s failed sending to %s: %s", notifier_name, phone, exc)

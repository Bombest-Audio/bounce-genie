"""BatchRunner – orchestrates the full batch bounce workflow."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bounce_genie.adapters.base import IDawAdapter
from bounce_genie.models import BounceJob
from bounce_genie.naming import apply_routing, render_name
from bounce_genie.notifications.base import BaseNotifier, BatchResult
from bounce_genie.queue import JobQueue

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchRunner:
    """Drives the full batch bounce workflow.

    Typical usage::

        from bounce_genie import BatchRunner, BounceJob, JobQueue
        from bounce_genie.adapters import ProToolsAdapter
        from bounce_genie.notifications import EmailNotifier

        queue = JobQueue()
        queue.add_many([
            BounceJob(session_path="~/sessions/song1.ptx"),
            BounceJob(session_path="~/sessions/song2.ptx"),
        ])

        runner = BatchRunner(
            adapter=ProToolsAdapter(),
            queue=queue,
            notifiers=[EmailNotifier()],
        )
        runner.run()

    Parameters
    ----------
    adapter:
        The DAW adapter to use for all jobs in this batch.
    queue:
        Job queue containing the sessions to process.
    notifiers:
        Zero or more notifiers that receive the batch result.
    pause_on_error:
        When *True* (default), the runner stops on the first failed job
        rather than continuing to the next one.
    """

    def __init__(
        self,
        adapter: IDawAdapter,
        queue: JobQueue,
        notifiers: list[BaseNotifier] | None = None,
        pause_on_error: bool = True,
    ) -> None:
        self._adapter = adapter
        self._queue = queue
        self._notifiers = notifiers or []
        self._pause_on_error = pause_on_error

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> BatchResult:
        """Process all jobs in the queue and return a summary.

        Returns
        -------
        BatchResult
            Summary of the completed batch (counts, outputs, errors).
        """
        result = BatchResult(total=len(self._queue))
        index = 0

        while not self._queue.is_empty():
            job = self._queue.next()
            if job is None:
                break
            try:
                outputs = self._process_job(job, index, total=result.total)
                result.outputs.extend(outputs)
                result.succeeded += 1
            except Exception as exc:
                error_msg = f"{job.session_path.name}: {exc}"
                logger.error("Job failed – %s", error_msg)
                result.failed += 1
                result.errors.append(error_msg)
                if self._pause_on_error:
                    logger.warning("Stopping batch due to error (pause_on_error=True)")
                    break
            finally:
                index += 1

        self._notify(result)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_job(self, job: BounceJob, index: int, total: int = 0) -> list[Path]:
        """Execute a single bounce job and return the final output paths."""
        logger.info(
            "Processing job %d/%d: %s",
            index + 1,
            total,
            job.session_path,
        )

        self._adapter.open_session(job.session_path)
        try:
            self._adapter.prep_bounce(
                job.options.selection_strategy,
                job.options,
            )
            self._adapter.execute_bounce(job.options)
            raw_outputs = self._adapter.detect_outputs(job)
        finally:
            self._adapter.close_session()

        rendered = render_name(job.naming_template, job, index=index)
        final_outputs = apply_routing(raw_outputs, job, rendered)
        return final_outputs

    def _notify(self, result: BatchResult) -> None:
        """Dispatch notifications to all configured notifiers."""
        # Collect all unique notification targets
        targets: set[str] = set()
        # We re-walk the original queue – it's empty now, so gather from result context.
        # Notifiers without a specific recipient get sent to a placeholder that
        # individual implementations can override.
        for notifier in self._notifiers:
            try:
                notifier.send(result, recipient="")
            except Exception as exc:
                logger.error("Notifier %s failed: %s", type(notifier).__name__, exc)

    def run_job(self, job: BounceJob, index: int = 0) -> list[Path]:
        """Run a single job outside of the queue.  Useful for testing."""
        return self._process_job(job, index, total=1)

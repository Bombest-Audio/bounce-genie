"""
bounce_genie.orchestrator – ties the whole pipeline together.

The :class:`BounceOrchestrator` is the "virtual intern": it iterates the
job queue, drives the appropriate DAW adapter for each session, detects
outputs, routes files, and dispatches notifications.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from .adapters import get_adapter_for_job
from .automation.engine import AutomationEngine
from .detector import BounceOutputDetector
from .models import BounceJob, JobStatus
from .naming import RoutingEngine
from .notifications.manager import NotificationManager
from .queue import BounceQueue

logger = logging.getLogger(__name__)


class BounceOrchestrator:
    """
    Processes all jobs in a :class:`BounceQueue` sequentially.

    Parameters
    ----------
    queue:
        The job queue to drain.
    automation_engine:
        The UI automation backend.  Defaults to a ``dry_run`` engine if
        not provided (useful for testing).
    notification_manager:
        Optional notification dispatcher.
    bounce_timeout:
        Maximum seconds to wait for a single bounce to complete.
    routing_engine:
        Optional custom routing engine for naming/copying outputs.
    """

    def __init__(
        self,
        queue: BounceQueue,
        automation_engine: Optional[AutomationEngine] = None,
        notification_manager: Optional[NotificationManager] = None,
        bounce_timeout: float = 600.0,
        routing_engine: Optional[RoutingEngine] = None,
    ) -> None:
        self._queue = queue
        self._engine = automation_engine or AutomationEngine(dry_run=True)
        self._notifier = notification_manager or NotificationManager()
        self._bounce_timeout = bounce_timeout
        self._routing = routing_engine or RoutingEngine()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Process all pending jobs, then send the batch summary notification.
        """
        logger.info(
            "Orchestrator: starting batch – %d job(s) pending",
            self._queue.pending_count,
        )

        batch_index = 0
        while True:
            job = self._queue.next_pending()
            if job is None:
                break
            self._process_job(job, batch_index)
            batch_index += 1

        logger.info("Orchestrator: batch finished")
        self._notifier.send_batch_summary(self._queue.all_jobs)

    # ------------------------------------------------------------------
    # Per-job processing
    # ------------------------------------------------------------------

    def _process_job(self, job: BounceJob, batch_index: int) -> None:
        logger.info(
            "Orchestrator: processing job %s (%s)",
            job.id,
            job.session_path,
        )
        try:
            adapter = get_adapter_for_job(job, self._engine)

            # 1. Open the session
            adapter.open_session(job.session_path)

            # 2. Prepare the bounce dialog
            adapter.prep_bounce(
                job.options.selection_strategy,
                job.options,
            )

            # 3. Start watching for output files BEFORE executing the bounce
            bounce_dirs = self._candidate_bounce_dirs(job)
            detectors = [BounceOutputDetector(d) for d in bounce_dirs]
            for det in detectors:
                det.start()

            # 4. Execute the bounce
            adapter.execute_bounce(job.options)

            # 5. Wait for output detection (or fall back to adapter.detect_outputs)
            output_files: List[Path] = []
            for det in detectors:
                found = det.wait_for_new_files(timeout=self._bounce_timeout)
                output_files.extend(found)
                det.stop()

            if not output_files:
                # Fall back to adapter's own detection logic
                output_files = adapter.detect_outputs(job)

            job.output_files = output_files
            logger.info(
                "Orchestrator: job %s produced %d file(s)",
                job.id,
                len(output_files),
            )

            # 6. Route / copy outputs
            if job.copy_dest:
                routed: List[Path] = []
                for src in output_files:
                    dst = self._routing.route(src, job, batch_index=batch_index)
                    routed.append(dst)
                job.output_files = routed

            # 7. Mark complete and notify
            self._queue.mark_completed(job)
            self._notifier.send_job_complete(job)

        except FileNotFoundError as exc:
            logger.error("Orchestrator: job %s – file not found: %s", job.id, exc)
            self._queue.mark_failed(job, str(exc))
        except Exception as exc:
            logger.exception("Orchestrator: job %s – unexpected error: %s", job.id, exc)
            self._queue.mark_failed(job, str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _candidate_bounce_dirs(self, job: BounceJob) -> List[Path]:
        """Return directories to watch for bounce output files."""
        dirs = [
            job.session_path.parent / "Bounced Files",  # Pro Tools default
            job.session_path.parent / "Bounces",         # Logic default
            job.session_path.parent / "Audio",           # Cubase default
            job.session_path.parent,                     # Ableton default / fallback
        ]
        if job.copy_dest:
            dirs.append(job.copy_dest)
        return dirs

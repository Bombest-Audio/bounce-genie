"""
bounce_genie.cli – command-line interface.

Usage
-----
::

    bounce-genie --help
    bounce-genie run session1.ptx session2.ptx --email me@example.com
    bounce-genie run *.logicx --copy-to ~/Dropbox/Bounces --dry-run
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import BounceJob, BounceOptions, BounceQueue, DawType, NotificationTarget
from .automation.engine import AutomationEngine
from .models import AudioFormat, SelectionStrategy
from .notifications.manager import NotificationManager
from .orchestrator import BounceOrchestrator

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bounce-genie",
        description="Batch bounce automation for DAWs.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── run ──────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser("run", help="Run a batch bounce job.")
    run_parser.add_argument(
        "sessions",
        nargs="+",
        metavar="SESSION",
        help="Paths to session files to bounce.",
    )
    run_parser.add_argument(
        "--email",
        metavar="ADDRESS",
        help="Email address to notify when the batch is done.",
    )
    run_parser.add_argument(
        "--phone",
        metavar="E164",
        help="Phone number (E.164) for SMS notification (requires twilio extra).",
    )
    run_parser.add_argument(
        "--copy-to",
        metavar="DIR",
        help="Copy finished bounces to this directory.",
    )
    run_parser.add_argument(
        "--template",
        default="{session_name}",
        help="Output filename template (default: '{session_name}').",
    )
    run_parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=[f.value for f in AudioFormat],
        help="Output format(s); may be specified multiple times.",
    )
    run_parser.add_argument(
        "--daw",
        choices=[d.value for d in DawType],
        help="Force a specific DAW adapter (auto-detected by default).",
    )
    run_parser.add_argument(
        "--offline",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use offline (faster-than-real-time) bounce where supported.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Log actions without driving the DAW UI.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        return _cmd_run(args)

    parser.print_help()
    return 1


def _cmd_run(args: argparse.Namespace) -> int:
    notification_target = NotificationTarget(
        email=args.email,
        phone_number=args.phone,
    )

    formats = (
        [AudioFormat(f) for f in args.formats]
        if args.formats
        else [AudioFormat.WAV]
    )

    daw_type = DawType(args.daw) if args.daw else None
    copy_dest = Path(args.copy_to) if args.copy_to else None

    options = BounceOptions(
        formats=formats,
        offline=args.offline,
        daw_type=daw_type,
    )

    queue = BounceQueue()
    for session in args.sessions:
        job = BounceJob(
            session_path=Path(session),
            naming_template=args.template,
            copy_dest=copy_dest,
            notification_target=notification_target,
            options=options,
        )
        queue.add(job)

    engine = AutomationEngine(dry_run=args.dry_run)
    manager = NotificationManager()

    if args.email:
        from .notifications.email_notifier import EmailNotifier, SmtpConfig
        manager.register(EmailNotifier(SmtpConfig()))

    if args.phone:
        logger.warning(
            "SMS notifications require manual TwilioConfig setup; skipping."
        )

    orchestrator = BounceOrchestrator(
        queue=queue,
        automation_engine=engine,
        notification_manager=manager,
    )
    orchestrator.run()

    failed = queue.failed_jobs
    if failed:
        logger.error("%d job(s) failed:", len(failed))
        for job in failed:
            logger.error("  %s: %s", job.session_path, job.error)
        return 1

    logger.info("All jobs completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

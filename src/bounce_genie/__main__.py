"""Command-line entry point for Bounce Genie."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from bounce_genie.models import BounceJob, BounceOptions, NotificationTarget, SelectionStrategy
from bounce_genie.queue import JobQueue


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bounce-genie",
        description="Batch bounce/export automation for DAWs.",
    )
    parser.add_argument(
        "sessions",
        nargs="+",
        metavar="SESSION",
        help="One or more DAW session/project files to bounce.",
    )
    parser.add_argument(
        "--daw",
        choices=["protools", "logic", "cubase", "ableton"],
        default="protools",
        help="Target DAW (default: protools).",
    )
    parser.add_argument(
        "--template",
        default="${session_name}",
        help="Output filename template (default: '{session_name}').",
    )
    parser.add_argument(
        "--copy-dest",
        metavar="DIR",
        help="Copy finished bounces to this directory.",
    )
    parser.add_argument(
        "--email",
        metavar="ADDRESS",
        help="Email address for completion notification.",
    )
    parser.add_argument(
        "--sms",
        metavar="PHONE",
        help="Phone number (E.164) for SMS completion notification.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without driving any real UI.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Build the adapter
    from bounce_genie.automation.engine import AutomationEngine  # noqa: PLC0415
    engine = AutomationEngine(dry_run=args.dry_run)

    if args.daw == "protools":
        from bounce_genie.adapters.protools import ProToolsAdapter  # noqa: PLC0415
        adapter = ProToolsAdapter(engine=engine)
    elif args.daw == "logic":
        from bounce_genie.adapters.logic import LogicAdapter  # noqa: PLC0415
        adapter = LogicAdapter(engine=engine)
    elif args.daw == "cubase":
        from bounce_genie.adapters.cubase import CubaseAdapter  # noqa: PLC0415
        adapter = CubaseAdapter(engine=engine)
    else:
        from bounce_genie.adapters.ableton import AbletonAdapter  # noqa: PLC0415
        adapter = AbletonAdapter(engine=engine)

    # Build notifiers
    notifiers = []
    if args.email:
        from bounce_genie.notifications.email import EmailNotifier  # noqa: PLC0415
        notifiers.append(EmailNotifier())
    if args.sms:
        from bounce_genie.notifications.sms import SmsNotifier, TwilioConfig  # noqa: PLC0415
        import os  # noqa: PLC0415
        config = TwilioConfig(
            account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
            from_number=os.environ.get("TWILIO_FROM_NUMBER", ""),
        )
        notifiers.append(SmsNotifier(config=config))

    # Build the queue
    notification_target = NotificationTarget(email=args.email, phone=args.sms)
    queue = JobQueue()
    for session in args.sessions:
        queue.add(
            BounceJob(
                session_path=Path(session),
                naming_template=args.template,
                copy_dest=Path(args.copy_dest) if args.copy_dest else None,
                notification_target=notification_target,
                options=BounceOptions(),
            )
        )

    # Run!
    from bounce_genie.runner import BatchRunner  # noqa: PLC0415
    runner = BatchRunner(adapter=adapter, queue=queue, notifiers=notifiers)
    result = runner.run()

    print(result.summary_text())
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

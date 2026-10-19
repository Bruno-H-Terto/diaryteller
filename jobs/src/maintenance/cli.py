"""Command-line entry points for maintenance jobs."""

from __future__ import annotations

import argparse
import asyncio
import json

from diary_observability import configure_logging

from maintenance.backup_mongo import backup_mongo
from maintenance.backup_postgres import backup_postgres
from maintenance.billing_reconcile import reconcile
from maintenance.restore_check import verify_latest
from maintenance.retention import run_retention
from maintenance.scheduler import run_scheduler
from maintenance.settings import get_settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="diary-maintenance")
    parser.add_argument(
        "command",
        choices=[
            "retention",
            "reconcile-billing",
            "backup-postgres",
            "backup-mongo",
            "restore-check",
            "schedule",
        ],
    )
    return parser


async def _run(command: str) -> object:
    settings = get_settings()
    configure_logging("maintenance", "0.1.0")
    if command == "retention":
        return await run_retention(settings)
    if command == "reconcile-billing":
        return await reconcile(settings)
    if command == "backup-postgres":
        return str(await backup_postgres(settings))
    if command == "backup-mongo":
        return str(await backup_mongo(settings))
    if command == "restore-check":
        return await verify_latest(settings)
    return await run_scheduler(settings)


def main() -> None:
    """Parse a subcommand and print a JSON summary."""
    args = _parser().parse_args()
    result = asyncio.run(_run(args.command))
    print(json.dumps(result, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

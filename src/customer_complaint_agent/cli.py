"""Command-line interface for the customer email agent."""

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict

from .harness.runner import RunResult
from .runtime.email_handler import run_email_handler

EmailHandler = Callable[[str], RunResult]


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="customer-complaint-agent",
        description="Process customer emails with a sample AI agent.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="customer-complaint-agent 0.1.0",
    )
    parser.add_argument(
        "--email-id",
        "--email_id",
        dest="email_id",
        help="Identifier of the email to handle.",
    )
    return parser


def main(
    argv: list[str] | None = None,
    email_handler: EmailHandler = run_email_handler,
) -> int:
    """Run the command-line application."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.email_id is None:
        parser.print_help()
        return 0

    result = email_handler(arguments.email_id)
    result_data = asdict(result)
    output = json.dumps(result_data, indent=2)
    print(output)

    return 0

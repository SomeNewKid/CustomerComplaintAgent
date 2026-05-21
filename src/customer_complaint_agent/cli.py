"""Command-line interface for the customer complaint agent."""

import argparse


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="customer-complaint-agent",
        description="Process customer complaints with a sample AI agent.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="customer-complaint-agent 0.1.0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application."""
    parser = _build_parser()
    parser.parse_args(argv)
    return 0

"""Runtime settings shared across the agentic system."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configuration supplied by the harness at runtime."""

    attachments_directory: Path
    max_turns: int

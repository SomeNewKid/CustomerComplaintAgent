"""Runtime settings wiring."""

from pathlib import Path

from customer_complaint_agent.shared.settings import Settings


def create_settings() -> Settings:
    """Create settings for the email handling runtime."""
    return Settings(
        attachments_directory=Path("data/attachments"),
        max_agent_turns=10,
        max_paid_model_calls=10,
    )

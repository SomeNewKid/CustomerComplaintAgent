"""Runtime model client wiring."""

from customer_complaint_agent.infrastructure.openai_client import OpenAIClient
from customer_complaint_agent.shared.model import (
    ModelCallBudget,
    ModelClientRegistration,
    ModelClientRegistry,
)
from customer_complaint_agent.shared.settings import Settings


def create_model_client_registry(settings: Settings) -> ModelClientRegistry:
    """Create model clients for the email handling runtime."""
    return ModelClientRegistry(
        model_call_budget=ModelCallBudget(
            max_paid_model_calls=settings.max_paid_model_calls,
        ),
        clients=(
            ModelClientRegistration(
                name="openai",
                client=OpenAIClient(),
                is_text_enabled=True,
                is_vision_enabled=True,
                is_paid=True,
            ),
        ),
    )

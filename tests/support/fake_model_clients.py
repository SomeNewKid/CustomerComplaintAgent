"""Fake model clients used by unit tests."""

from customer_complaint_agent.shared.model import (
    ModelClientRegistration,
    ModelClientRegistry,
    ModelRequest,
    ModelResponse,
)


class FakeVisionModelClient:
    """Vision model fake that classifies damage from the image filename."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return deterministic damage verification data."""
        filename = request.image_paths[0].name
        normalized_filename = filename.casefold()
        damage_verified = (
            "broken" in normalized_filename and "unbroken" not in normalized_filename
        )

        if damage_verified:
            supporting_text = "The filename indicates a broken product."
        else:
            supporting_text = "The filename does not indicate a broken product."

        return ModelResponse(
            data={
                "damage_verified": damage_verified,
                "confidence": 1.0,
                "supporting_text": supporting_text,
            }
        )


class ScriptedTextModelClient:
    """Text model fake that returns scripted responses."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.requests: list[ModelRequest] = []
        self._responses = responses

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return the next scripted response."""
        self.requests.append(request)

        if not self._responses:
            raise RuntimeError("No scripted model response is available.")

        return self._responses.pop(0)


def create_fake_vision_model_registry() -> ModelClientRegistry:
    """Create a registry containing one free fake vision model."""
    return ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="fake_vision",
                client=FakeVisionModelClient(),
                is_text_enabled=False,
                is_vision_enabled=True,
                is_paid=False,
            ),
        )
    )

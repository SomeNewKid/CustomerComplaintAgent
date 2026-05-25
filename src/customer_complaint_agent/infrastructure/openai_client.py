"""OpenAI implementation of the shared model client."""

import base64
import importlib
import json
import mimetypes
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from customer_complaint_agent.shared.model import (
    ModelClient,
    ModelRequest,
    ModelResponse,
)

_DEFAULT_MODEL = "gpt-5.4-mini"


class OpenAIClient:
    """Model client backed by the OpenAI Responses API."""

    def __init__(self, model: str | None = None) -> None:
        """Create the client with an optional model override."""
        openai_module = importlib.import_module("openai")
        openai_client_type = cast(
            Callable[[], object],
            openai_module.OpenAI,
        )
        self._client = openai_client_type()
        self._model = model or _DEFAULT_MODEL

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return a structured model response."""
        client = cast(Any, self._client)
        response = client.responses.create(
            model=self._model,
            instructions=request.system_prompt,
            input=[
                {
                    "role": "user",
                    "content": self._create_user_content(request),
                }
            ],
            text=self._create_text_options(request),
        )
        output_text = cast(str, response.output_text)

        if not output_text:
            return ModelResponse(data={})

        response_data = parse_response_output_text(output_text)

        return ModelResponse(data=response_data)

    def _create_user_content(self, request: ModelRequest) -> list[dict[str, object]]:
        content: list[dict[str, object]] = [
            {
                "type": "input_text",
                "text": json.dumps(
                    {
                        "prompt": request.user_prompt,
                        "input_data": request.input_data,
                    }
                ),
            }
        ]

        for image_path in request.image_paths:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._data_url_from_image_path(image_path),
                }
            )

        return content

    def _create_text_options(
        self,
        request: ModelRequest,
    ) -> dict[str, object] | None:
        if request.response_schema is None:
            return None

        return {
            "format": {
                "type": "json_schema",
                "name": request.response_schema_name,
                "schema": request.response_schema,
                "strict": True,
            }
        }

    def _data_url_from_image_path(self, image_path: Path) -> str:
        mime_type = (
            mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        )
        image_bytes = image_path.read_bytes()
        encoded_image = base64.b64encode(image_bytes)
        image_data = encoded_image.decode("ascii")
        return f"data:{mime_type};base64,{image_data}"


def create_openai_client(model: str | None = None) -> ModelClient:
    """Create an OpenAI-backed model client."""
    return OpenAIClient(model=model)


def parse_response_output_text(output_text: str) -> dict[str, object]:
    """Parse structured output text from the Responses API."""
    try:
        output_data = json.loads(output_text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        output_data, _ = decoder.raw_decode(output_text)

    if not isinstance(output_data, dict):
        raise ValueError("OpenAI response output text must contain a JSON object.")

    return cast(dict[str, object], output_data)

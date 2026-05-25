import pytest

from customer_complaint_agent.infrastructure.openai_client import (
    parse_response_output_text,
)


def test_parse_response_output_text_parses_json_object() -> None:
    output_text = '{"result": "ok", "count": 2}'

    data = parse_response_output_text(output_text)

    assert data == {"result": "ok", "count": 2}


def test_parse_response_output_text_uses_first_json_object_with_extra_data() -> None:
    output_text = '{"result": "ok"}{"extra": "ignored"}'

    data = parse_response_output_text(output_text)

    assert data == {"result": "ok"}


def test_parse_response_output_text_rejects_json_array() -> None:
    output_text = '["not", "an", "object"]'

    with pytest.raises(
        ValueError,
        match="OpenAI response output text must contain a JSON object.",
    ):
        parse_response_output_text(output_text)

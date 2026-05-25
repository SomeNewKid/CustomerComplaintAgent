"""Integration tests for the production email handler runtime."""

import os

import pytest

from customer_complaint_agent.harness.runner import RunStatus
from customer_complaint_agent.runtime.email_handler import run_email_handler

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_OPENAI_INTEGRATION_TESTS") != "1",
    reason="OpenAI integration tests require RUN_OPENAI_INTEGRATION_TESTS=1.",
)


def test_openai_email_handler_refunds_e001_damaged_cheap_item() -> None:
    result = run_email_handler("E001")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "refund",
        "reason_code": "damaged_cheap_item",
    }


def test_openai_email_handler_escalates_e002_damaged_expensive_item() -> None:
    result = run_email_handler("E002")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "escalate",
        "reason_code": "damaged_expensive_item",
    }

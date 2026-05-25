"""Integration tests for the OpenAI-backed complaint agent."""

import os

import pytest

from customer_complaint_agent.agents.llm_complaint_agent import LlmComplaintAgent
from customer_complaint_agent.harness.runner import RunStatus
from customer_complaint_agent.infrastructure.openai_client import OpenAIClient
from customer_complaint_agent.runtime.agent_registry import AgentRegistry
from customer_complaint_agent.runtime.email_handler import (
    run_email_handler_with_dependencies,
)
from customer_complaint_agent.shared.model import (
    ModelCallBudget,
    ModelClientRegistration,
    ModelClientRegistry,
)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_OPENAI_INTEGRATION_TESTS") != "1",
    reason="OpenAI integration tests require RUN_OPENAI_INTEGRATION_TESTS=1.",
)


def test_openai_llm_complaint_agent_refunds_e001_damaged_cheap_item() -> None:
    model_client_registry = _model_client_registry()
    agent_registry = AgentRegistry(
        agents={
            "complaint_agent": LlmComplaintAgent(model_client_registry),
        }
    )

    result = run_email_handler_with_dependencies(
        "E001",
        model_client_registry,
        agent_registry=agent_registry,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "refund",
        "reason_code": "damaged_cheap_item",
    }


def test_openai_llm_complaint_agent_escalates_e002_damaged_expensive_item() -> None:
    model_client_registry = _model_client_registry()
    agent_registry = AgentRegistry(
        agents={
            "complaint_agent": LlmComplaintAgent(model_client_registry),
        }
    )

    result = run_email_handler_with_dependencies(
        "E002",
        model_client_registry,
        agent_registry=agent_registry,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "escalate",
        "reason_code": "damaged_expensive_item",
    }


def _model_client_registry() -> ModelClientRegistry:
    return ModelClientRegistry(
        model_call_budget=ModelCallBudget(max_paid_model_calls=10),
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

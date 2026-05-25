from customer_complaint_agent.agents.llm_complaint_agent import LlmComplaintAgent
from customer_complaint_agent.harness.runner import RunStatus
from customer_complaint_agent.runtime.agent_registry import AgentRegistry
from customer_complaint_agent.runtime.email_handler import (
    run_email_handler_with_dependencies,
)
from customer_complaint_agent.shared.agent import (
    AgentDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.model import (
    ModelClientRegistration,
    ModelClientRegistry,
    ModelResponse,
)
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.validation import ValidationRule
from tests.support.fake_model_clients import (
    FakeVisionModelClient,
    ScriptedTextModelClient,
    create_fake_vision_model_registry,
)


class _RegistryInjectedAgent:
    name = "complaint_agent"

    def decide(self, request: AgentRequest) -> AgentDecision:
        return FinalDecision(
            completion_type="done",
            details={"source": "injected_agent"},
            reason="Injected agent handled the goal.",
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        return []


def test_email_handler_routes_e001_to_complaint_agent() -> None:
    result = _run_email_handler("E001")

    assert "refund_decision" in result.details


def test_email_handler_routes_e002_to_complaint_agent() -> None:
    result = _run_email_handler("E002")

    assert "refund_decision" in result.details


def test_email_handler_routes_e003_to_compliment_agent() -> None:
    result = _run_email_handler("E003")

    assert result.details["email_template"] == "reply_to_happy_customer"


def test_email_handler_routes_e004_to_compliment_agent() -> None:
    result = _run_email_handler("E004")

    assert result.details["email_template"] == "reply_to_happy_customer"


def test_email_handler_loop_completes_for_e001() -> None:
    result = _run_email_handler("E001")

    assert result.status == RunStatus.COMPLETED


def test_email_handler_loop_completes_for_e002() -> None:
    result = _run_email_handler("E002")

    assert result.status == RunStatus.COMPLETED


def test_email_handler_loop_completes_for_e003() -> None:
    result = _run_email_handler("E003")

    assert result.status == RunStatus.COMPLETED


def test_email_handler_loop_completes_for_e004() -> None:
    result = _run_email_handler("E004")

    assert result.status == RunStatus.COMPLETED


def test_email_handler_returns_run_id_for_e001() -> None:
    result = _run_email_handler("E001")

    assert result.run_id


def test_email_handler_returns_run_id_for_e002() -> None:
    result = _run_email_handler("E002")

    assert result.run_id


def test_email_handler_returns_run_id_for_e003() -> None:
    result = _run_email_handler("E003")

    assert result.run_id


def test_email_handler_returns_run_id_for_e004() -> None:
    result = _run_email_handler("E004")

    assert result.run_id


def test_email_handler_refunds_e001_damaged_cheap_item() -> None:
    result = _run_email_handler("E001")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "refund",
        "reason_code": "damaged_cheap_item",
    }


def test_email_handler_escalates_e002_damaged_expensive_item() -> None:
    result = _run_email_handler("E002")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "escalate",
        "reason_code": "damaged_expensive_item",
    }


def test_email_handler_replies_to_e003_happy_customer() -> None:
    result = _run_email_handler("E003")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details["email_template"] == "reply_to_happy_customer"
    assert result.details.get("email_customization") in (None, "")


def test_email_handler_replies_to_e004_happy_customer_photo() -> None:
    result = _run_email_handler("E004")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "email_template": "reply_to_happy_customer",
        "email_customization": "Thank customer for photo of necklace",
    }


def test_email_handler_uses_supplied_agent_registry() -> None:
    agent_registry = AgentRegistry(
        agents={
            "complaint_agent": _RegistryInjectedAgent(),
        }
    )

    result = run_email_handler_with_dependencies(
        "E001",
        create_fake_vision_model_registry(),
        agent_registry=agent_registry,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.details == {"source": "injected_agent"}


def test_email_handler_with_llm_complaint_agent_refunds_e001() -> None:
    scripted_text_model = ScriptedTextModelClient(
        responses=[
            _action_response("get_email", {"email_id": "E001"}),
            _action_response("get_order", {"order_id": "O001"}),
            _action_response("get_product", {"product_id": "P001"}),
            _action_response("verify_damaged_product", {"filename": "broken-mug.jpg"}),
            _action_response(
                "evaluate_refund_policy",
                {
                    "already_refunded": False,
                    "product_price": 12.0,
                    "damage_verified": True,
                },
            ),
            _final_response(
                {
                    "refund_decision": "refund",
                    "reason_code": "damaged_cheap_item",
                }
            ),
        ]
    )
    model_client_registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="fake_text",
                client=scripted_text_model,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
            ModelClientRegistration(
                name="fake_vision",
                client=FakeVisionModelClient(),
                is_text_enabled=False,
                is_vision_enabled=True,
                is_paid=False,
            ),
        )
    )
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
    assert len(scripted_text_model.requests) == 6


def test_email_handler_with_llm_complaint_agent_escalates_e002() -> None:
    scripted_text_model = ScriptedTextModelClient(
        responses=[
            _action_response("get_email", {"email_id": "E002"}),
            _action_response("get_order", {"order_id": "O004"}),
            _action_response("get_product", {"product_id": "P002"}),
            _action_response(
                "verify_damaged_product",
                {"filename": "broken-necklace.jpg"},
            ),
            _action_response(
                "evaluate_refund_policy",
                {
                    "already_refunded": False,
                    "product_price": 850.0,
                    "damage_verified": True,
                },
            ),
            _final_response(
                {
                    "refund_decision": "escalate",
                    "reason_code": "damaged_expensive_item",
                }
            ),
        ]
    )
    model_client_registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="fake_text",
                client=scripted_text_model,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
            ModelClientRegistration(
                name="fake_vision",
                client=FakeVisionModelClient(),
                is_text_enabled=False,
                is_vision_enabled=True,
                is_paid=False,
            ),
        )
    )
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
    assert len(scripted_text_model.requests) == 6


def _run_email_handler(email_id: str):
    agent_registry = AgentRegistry()

    return run_email_handler_with_dependencies(
        email_id,
        create_fake_vision_model_registry(),
        agent_registry,
    )


def _action_response(tool_name: str, arguments: dict[str, object]) -> ModelResponse:
    return ModelResponse(
        data={
            "reason": f"Need to call {tool_name}.",
            "state_updates": [],
            "action_decision": {
                "tool_name": tool_name,
                "arguments": arguments,
            },
            "final_decision": None,
        }
    )


def _final_response(details: dict[str, object]) -> ModelResponse:
    return ModelResponse(
        data={
            "reason": "The complaint has been resolved.",
            "state_updates": [],
            "action_decision": None,
            "final_decision": {
                "completion_type": "done",
                "details": details,
            },
        }
    )

import pytest

from customer_complaint_agent.agents.llm_complaint_agent import LlmComplaintAgent
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.model import (
    ModelClient,
    ModelClientRegistration,
    ModelClientRegistry,
    ModelRequest,
    ModelResponse,
)
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalState,
    GoalStatus,
    ToolResult,
)
from customer_complaint_agent.shared.tool import (
    ToolArgument,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from tests.support.fake_model_clients import ScriptedTextModelClient


class _FakeTextModelClient:
    def __init__(self, response: ModelResponse) -> None:
        self.last_request: ModelRequest | None = None
        self._response = response

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return self._response


class _FakeTool:
    name = "get_email"
    description = "Retrieve an email by email_id."
    arguments = (
        ToolArgument(
            name="email_id",
            argument_type="string",
            description="The identifier of an email.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        raise NotImplementedError


def test_llm_complaint_agent_blocks_when_no_text_model_is_available() -> None:
    agent = LlmComplaintAgent(
        model_client_registry=ModelClientRegistry(clients=()),
    )

    decision = agent.decide(_agent_request())

    assert isinstance(decision, FinalDecision)
    assert decision.completion_type == "blocked"
    assert decision.details == {"reason_code": "model_client_not_available"}


def test_llm_complaint_agent_converts_model_action_decision() -> None:
    model_client = _FakeTextModelClient(
        ModelResponse(
            data={
                "reason": "Need to inspect the email.",
                "state_updates": [],
                "action_decision": {
                    "tool_name": "get_email",
                    "arguments": {"email_id": "E001"},
                },
                "final_decision": None,
            }
        )
    )
    agent = LlmComplaintAgent(
        model_client_registry=_model_registry(model_client),
    )

    decision = agent.decide(_agent_request())

    assert isinstance(decision, ActionDecision)
    assert decision.tool_name == "get_email"
    assert decision.arguments == {"email_id": "E001"}
    assert model_client.last_request is not None
    assert model_client.last_request.response_schema is not None
    assert "Agent goal:" in model_client.last_request.user_prompt


def test_llm_complaint_agent_uses_scripted_text_model_response() -> None:
    model_client = ScriptedTextModelClient(
        responses=[
            ModelResponse(
                data={
                    "reason": "Need to inspect the email.",
                    "state_updates": [],
                    "action_decision": {
                        "tool_name": "get_email",
                        "arguments": {"email_id": "E001"},
                    },
                    "final_decision": None,
                }
            )
        ]
    )
    agent = LlmComplaintAgent(
        model_client_registry=_model_registry(model_client),
    )

    decision = agent.decide(_agent_request())

    assert isinstance(decision, ActionDecision)
    assert decision.tool_name == "get_email"
    assert len(model_client.requests) == 1


def test_scripted_text_model_client_captures_prompt_and_schema() -> None:
    model_client = ScriptedTextModelClient(
        responses=[
            ModelResponse(
                data={
                    "reason": "Need to inspect the email.",
                    "state_updates": [],
                    "action_decision": {
                        "tool_name": "get_email",
                        "arguments": {"email_id": "E001"},
                    },
                    "final_decision": None,
                }
            )
        ]
    )
    agent = LlmComplaintAgent(
        model_client_registry=_model_registry(model_client),
    )

    agent.decide(_agent_request())

    assert len(model_client.requests) == 1
    model_request = model_client.requests[0]
    assert model_request.response_schema is not None
    assert "Agent goal:" in model_request.user_prompt
    assert "Available tools:" in model_request.user_prompt
    assert "get_email" in model_request.user_prompt


def test_scripted_text_model_client_raises_when_no_response_is_available() -> None:
    model_client = ScriptedTextModelClient(responses=[])
    agent = LlmComplaintAgent(
        model_client_registry=_model_registry(model_client),
    )

    with pytest.raises(
        RuntimeError,
        match="No scripted model response is available.",
    ):
        agent.decide(_agent_request())

    assert len(model_client.requests) == 1


def _model_registry(model_client: ModelClient) -> ModelClientRegistry:
    return ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="fake_text",
                client=model_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
        )
    )


def _tool_registry() -> ToolRegistry:
    return ToolRegistry(tools=(_FakeTool(),))


def _agent_request() -> AgentRequest:
    return AgentRequest(
        goal_state=_goal_state(),
        tool_registry=_tool_registry(),
    )


def _goal_state() -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=[],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )

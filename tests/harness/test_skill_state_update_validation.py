"""Harness tests for skill-based state update validation."""

from pathlib import Path

from customer_complaint_agent.agents.skill_validation import SkillStateUpdateRule
from customer_complaint_agent.agents.skills import COMPLAINT_EMAIL_SKILL
from customer_complaint_agent.harness.runner import AgentHarness, RunStatus
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentDecision,
    AgentRequest,
    FinalDecision,
    StateUpdate,
)
from customer_complaint_agent.shared.model import ModelClientRegistry
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.settings import Settings
from customer_complaint_agent.shared.state import EntityRef, GoalState, GoalStatus
from customer_complaint_agent.shared.tool import (
    ToolArgument,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from customer_complaint_agent.shared.validation import ValidationRule


class _InvalidClaimAgent:
    name = "invalid_claim_agent"

    def decide(self, request: AgentRequest) -> AgentDecision:
        if request.goal_state.tool_results:
            return FinalDecision(
                completion_type="done",
                details={
                    "refund_decision": "refund",
                    "reason_code": "damaged_cheap_item",
                },
                reason="The complaint has been resolved.",
            )

        return ActionDecision(
            tool_name="fake_tool",
            arguments={"value": "example"},
            reason="Record an invalid claim before calling the tool.",
            state_updates=[
                StateUpdate(
                    operation="add_claim",
                    arguments={
                        "claim_type": "wrong_size",
                        "data": {"supporting_text": "the mug is too large"},
                    },
                )
            ],
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        return [SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)]

    def get_state_reducers(self) -> list[StateReducer]:
        return []


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by skill validation harness tests."
    arguments = (
        ToolArgument(
            name="value",
            argument_type="string",
            description="A fake tool value.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ):
        raise AssertionError("The tool should not run after validation fails.")


def test_harness_rejects_skill_disallowed_state_update() -> None:
    goal_state = _goal_state()
    agent_harness = AgentHarness()

    result = agent_harness.run_agent_goal(
        agent=_InvalidClaimAgent(),
        goal_state=goal_state,
        tool_registry=ToolRegistry(tools=(_FakeTool(),)),
        model_client_registry=ModelClientRegistry(clients=()),
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=2,
            max_paid_model_calls=0,
        ),
    )

    assert result.status == RunStatus.FAILED
    assert goal_state.claims == []
    assert goal_state.tool_results == []


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

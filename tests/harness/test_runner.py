from pathlib import Path

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
from customer_complaint_agent.shared.state import (
    Claim,
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
from customer_complaint_agent.shared.validation import ValidationRule


class _ToolUsingAgent:
    name = "tool_using_agent"

    def __init__(self, reducers: list[StateReducer] | None = None) -> None:
        self._reducers = reducers or []

    def decide(self, request: AgentRequest) -> AgentDecision:
        if request.goal_state.tool_results:
            return FinalDecision(
                completion_type="done",
                details={"tool_result_count": len(request.goal_state.tool_results)},
                reason="The tool result is available.",
            )

        return ActionDecision(
            tool_name="fake_tool",
            arguments={"value": "example"},
            reason="Need to call the fake tool.",
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        return self._reducers


class _ClaimingToolUsingAgent:
    name = "claiming_tool_using_agent"

    def decide(self, request: AgentRequest) -> AgentDecision:
        if request.goal_state.tool_results:
            return FinalDecision(
                completion_type="done",
                details={"claim_count": len(request.goal_state.claims)},
                reason="The claim and tool result are available.",
            )

        return ActionDecision(
            tool_name="claim_aware_tool",
            arguments={"value": "example"},
            reason="Record a claim before calling the tool.",
            state_updates=[
                StateUpdate(
                    operation="add_claim",
                    arguments={
                        "claim_type": "damaged_product",
                        "data": {"supporting_text": "the handle is broken"},
                    },
                )
            ],
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        return []


class _CustomerReferenceReducer:
    def apply(
        self,
        goal_state: GoalState,
        tool_result: ToolResult,
    ) -> None:
        goal_state.set_entity_reference(
            EntityRef(entity_type="customer", entity_id="C001")
        )


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by harness runner tests."
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
    ) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"value": "tool response"},
        )


class _ClaimAwareTool:
    name = "claim_aware_tool"
    description = "Fake tool that observes claim state during execution."
    arguments = (
        ToolArgument(
            name="value",
            argument_type="string",
            description="A fake tool value.",
        ),
    )

    def __init__(self, goal_state: GoalState) -> None:
        self._goal_state = goal_state

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"claim_count_at_execution": len(self._goal_state.claims)},
        )


def test_agent_loop_continues_after_action_decision() -> None:
    goal_state = _goal_state()

    agent_harness = AgentHarness()
    result = agent_harness.run_agent_goal(
        agent=_ToolUsingAgent(),
        goal_state=goal_state,
        tool_registry=ToolRegistry(tools=(_FakeTool(),)),
        model_client_registry=ModelClientRegistry(clients=()),
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=2,
            max_paid_model_calls=0,
        ),
    )

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {"tool_result_count": 1}
    assert goal_state.tool_results == [
        ToolResult(
            tool_name="fake_tool",
            arguments={"value": "example"},
            data={"value": "tool response"},
        )
    ]


def test_agent_loop_applies_state_reducers_after_action_decision() -> None:
    goal_state = _goal_state()

    agent_harness = AgentHarness()
    result = agent_harness.run_agent_goal(
        agent=_ToolUsingAgent(reducers=[_CustomerReferenceReducer()]),
        goal_state=goal_state,
        tool_registry=ToolRegistry(tools=(_FakeTool(),)),
        model_client_registry=ModelClientRegistry(clients=()),
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=2,
            max_paid_model_calls=0,
        ),
    )

    assert result.status == RunStatus.COMPLETED
    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="customer", entity_id="C001"),
    ]


def test_agent_loop_applies_state_updates_before_action_decision() -> None:
    goal_state = _goal_state()

    agent_harness = AgentHarness()
    result = agent_harness.run_agent_goal(
        agent=_ClaimingToolUsingAgent(),
        goal_state=goal_state,
        tool_registry=ToolRegistry(tools=(_ClaimAwareTool(goal_state),)),
        model_client_registry=ModelClientRegistry(clients=()),
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=2,
            max_paid_model_calls=0,
        ),
    )

    assert result.status == RunStatus.COMPLETED
    assert goal_state.claims == [
        Claim(
            claim_type="damaged_product",
            data={"supporting_text": "the handle is broken"},
        )
    ]
    assert goal_state.tool_results == [
        ToolResult(
            tool_name="claim_aware_tool",
            arguments={"value": "example"},
            data={"claim_count_at_execution": 1},
        )
    ]


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

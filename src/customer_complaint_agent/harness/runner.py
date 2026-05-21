"""Agent harness entry points."""

from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from customer_complaint_agent.shared.agent import (
    ActionDecision,
    Agent,
    AgentDecision,
    AgentRequest,
    FinalDecision,
    StateUpdate,
)
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.settings import Settings
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalResult,
    GoalState,
    GoalStatus,
)
from customer_complaint_agent.shared.tool import ToolRegistry, ToolRuntime
from customer_complaint_agent.shared.validation import ValidationResult

from .rules import HARNESS_VALIDATION_RULES, RegisteredToolRule
from .tool_executor import ToolExecutor
from .trace import Trace
from .validation import validate_decision


class RunStatus(StrEnum):
    """Public status of an agent harness run."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RunResult:
    """Public result of running an agent goal."""

    run_id: str
    status: RunStatus
    completion_type: str | None
    details: dict[str, object]


def run_agent_goal(
    agent: Agent,
    goal_state: GoalState,
    tool_registry: ToolRegistry,
    settings: Settings,
) -> RunResult:
    """Run one agent against one goal."""
    trace = Trace()
    tool_executor = ToolExecutor(tool_registry)
    tool_runtime = ToolRuntime(settings=settings)

    _run_agent_loop(
        agent,
        goal_state,
        tool_registry,
        tool_executor,
        tool_runtime,
        settings,
        trace,
    )

    if goal_state.status == GoalStatus.COMPLETED:
        result = goal_state.results[-1]
        return RunResult(
            run_id=goal_state.goal_id,
            status=RunStatus.COMPLETED,
            completion_type=result.result_type,
            details=result.data,
        )

    return RunResult(
        run_id=goal_state.goal_id,
        status=RunStatus.FAILED,
        completion_type=None,
        details={"agent": agent.name, "reason_code": "goal_not_completed"},
    )


def _run_agent_loop(
    agent: Agent,
    goal_state: GoalState,
    tool_registry: ToolRegistry,
    tool_executor: ToolExecutor,
    tool_runtime: ToolRuntime,
    settings: Settings,
    trace: Trace,
) -> None:
    done = False
    turns_completed = 0

    while not done and turns_completed < settings.max_turns:
        decision = agent.decide(AgentRequest(goal_state=goal_state))
        trace.event(agent.name, decision.reason)
        validation = _validate_agent_decision(
            agent,
            decision,
            goal_state,
            tool_registry,
        )

        if not validation.accepted:
            done = _apply_validation_failure(goal_state, validation, trace)
            turns_completed += 1
            continue

        _apply_state_updates(goal_state, decision.state_updates)

        if isinstance(decision, FinalDecision):
            done = _apply_final_decision(goal_state, decision, trace)
        elif isinstance(decision, ActionDecision):
            done = _apply_action_decision(
                goal_state,
                decision,
                agent.get_state_reducers(),
                tool_executor,
                tool_runtime,
                trace,
            )
        else:
            goal_state.status = GoalStatus.FAILED
            trace.event("harness", "Agent returned an unsupported decision.")
            done = True

        turns_completed += 1

    if not done:
        goal_state.status = GoalStatus.FAILED
        trace.event("harness", f"Stopped after reaching {settings.max_turns} turn.")


def _validate_agent_decision(
    agent: Agent,
    decision: AgentDecision,
    goal_state: GoalState,
    tool_registry: ToolRegistry,
) -> ValidationResult:
    validation = validate_decision(
        decision,
        goal_state,
        HARNESS_VALIDATION_RULES,
    )

    if not validation.accepted:
        return validation

    validation = validate_decision(
        decision,
        goal_state,
        [RegisteredToolRule(tool_registry)],
    )

    if not validation.accepted:
        return validation

    return validate_decision(
        decision,
        goal_state,
        agent.get_validation_rules(),
    )


def _apply_validation_failure(
    goal_state: GoalState,
    validation: ValidationResult,
    trace: Trace,
) -> bool:
    goal_state.status = GoalStatus.FAILED
    for error in validation.errors:
        trace.event("harness", f"Validation failed: {error.code}: {error.message}")
    return True


def _apply_state_updates(
    goal_state: GoalState,
    state_updates: list[StateUpdate],
) -> None:
    for state_update in state_updates:
        if state_update.operation == "add_claim":
            source = _entity_ref_from_argument(state_update.arguments["source"])
            goal_state.add_claim(
                claim_type=str(state_update.arguments["claim_type"]),
                source=source,
                supporting_text=str(state_update.arguments["supporting_text"]),
            )
        elif state_update.operation == "add_fact":
            source = _entity_ref_from_argument(state_update.arguments["source"])
            data = _dict_from_argument(state_update.arguments["data"])
            goal_state.add_fact(
                fact_type=str(state_update.arguments["fact_type"]),
                source=source,
                data=data,
            )
        elif state_update.operation == "add_output":
            data = _dict_from_argument(state_update.arguments["data"])
            goal_state.add_output(
                output_type=str(state_update.arguments["output_type"]),
                data=data,
            )


def _entity_ref_from_argument(value: object) -> EntityRef:
    source = _dict_from_argument(value)
    return EntityRef(
        entity_type=str(source["entity_type"]),
        entity_id=str(source["entity_id"]),
    )


def _dict_from_argument(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)


def _apply_final_decision(
    goal_state: GoalState,
    decision: FinalDecision,
    trace: Trace,
) -> bool:
    goal_state.status = GoalStatus.COMPLETED
    goal_state.results.append(
        GoalResult(
            result_type=decision.completion_type,
            data=decision.details,
        )
    )
    trace.event("harness", f"Accepted final decision: {decision.completion_type}.")
    return True


def _apply_action_decision(
    goal_state: GoalState,
    decision: ActionDecision,
    reducers: list[StateReducer],
    tool_executor: ToolExecutor,
    tool_runtime: ToolRuntime,
    trace: Trace,
) -> bool:
    tool_result = tool_executor.execute(
        decision.tool_name,
        decision.arguments,
        tool_runtime,
    )
    goal_state.tool_results.append(tool_result)

    for reducer in reducers:
        reducer.apply(goal_state, tool_result)

    trace.event("harness", f"Executed tool {decision.tool_name}.")
    return False

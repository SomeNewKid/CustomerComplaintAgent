from customer_complaint_agent.agents.deterministic_compliment_agent import (
    DeterministicComplimentAgent,
)
from customer_complaint_agent.shared.agent import AgentRequest, FinalDecision
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalState,
    GoalStatus,
    ToolResult,
)
from customer_complaint_agent.shared.tool import ToolRegistry


def test_deterministic_compliment_agent_blocks_when_email_is_not_found() -> None:
    decision = DeterministicComplimentAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    ToolResult(
                        tool_name="get_email",
                        arguments={"email_id": "E001"},
                        data={"email": None},
                    )
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    assert isinstance(decision, FinalDecision)
    assert decision.completion_type == "blocked"
    assert decision.details == {"reason_code": "email_not_found"}


def _goal_state(tool_results: list[ToolResult]) -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=tool_results,
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )

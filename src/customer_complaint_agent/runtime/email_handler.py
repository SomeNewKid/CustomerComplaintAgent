"""Runtime entry point for handling customer emails."""

from pathlib import Path

from customer_complaint_agent.domain.store import Store
from customer_complaint_agent.domain.tools import (
    GetCustomerTool,
    GetEmailTool,
    GetOrderTool,
    GetProductTool,
    VerifyDamagedProductTool,
)
from customer_complaint_agent.harness.runner import RunResult, RunStatus, run_agent_goal
from customer_complaint_agent.shared.settings import Settings
from customer_complaint_agent.shared.state import EntityRef, GoalState, GoalStatus
from customer_complaint_agent.shared.tool import Tool, ToolRegistry

from .agent_registry import AgentRegistry
from .agent_router import AgentRouter

_AGENT_TOOL_NAMES: dict[str, tuple[str, ...]] = {
    "complaint_agent": (
        GetEmailTool.name,
        GetOrderTool.name,
        GetProductTool.name,
        GetCustomerTool.name,
        VerifyDamagedProductTool.name,
    ),
    "compliment_agent": (
        GetEmailTool.name,
        VerifyDamagedProductTool.name,
    ),
}


def run_email_handler(email_id: str) -> RunResult:
    """Run the email handling runtime for one email."""
    store = Store()
    settings = _create_settings()
    email = store.get_email(email_id)
    goal_state = _create_email_goal_state(email_id)

    if email is None:
        return RunResult(
            run_id=goal_state.goal_id,
            status=RunStatus.FAILED,
            completion_type=None,
            details={"reason_code": "email_not_found"},
        )

    router = AgentRouter()
    route = router.route(email)

    registry = AgentRegistry()
    agent = registry.get(route.agent_name)

    if agent is None:
        return RunResult(
            run_id=goal_state.goal_id,
            status=RunStatus.FAILED,
            completion_type=None,
            details={"reason_code": "agent_not_found"},
        )

    tool_registry = _create_tool_registry(route.agent_name, store)

    return run_agent_goal(agent, goal_state, tool_registry, settings)


def _create_email_goal_state(email_id: str) -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id=email_id)
    return GoalState(
        goal_id=f"handle-email-{email_id}",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=[],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )


def _create_tool_registry(agent_name: str, store: Store) -> ToolRegistry:
    available_tools: dict[str, Tool] = {
        GetEmailTool.name: GetEmailTool(store),
        GetOrderTool.name: GetOrderTool(store),
        GetProductTool.name: GetProductTool(store),
        GetCustomerTool.name: GetCustomerTool(store),
        VerifyDamagedProductTool.name: VerifyDamagedProductTool(),
    }

    tools: list[Tool] = []

    for tool_name in _AGENT_TOOL_NAMES.get(agent_name, ()):
        tool = available_tools.get(tool_name)

        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not available.")

        tools.append(tool)

    return ToolRegistry(tools=tuple(tools))


def _create_settings() -> Settings:
    return Settings(
        attachments_directory=Path("data/attachments"),
        max_turns=3,
    )

"""Runtime entry point for handling customer emails."""

from pathlib import Path

from customer_complaint_agent.domain.store import Store
from customer_complaint_agent.domain.tools import (
    EvaluateRefundPolicyTool,
    GetCustomerTool,
    GetEmailTool,
    GetOrderTool,
    GetProductTool,
    VerifyDamagedProductTool,
)
from customer_complaint_agent.harness.runner import AgentHarness, RunResult, RunStatus
from customer_complaint_agent.infrastructure.openai_client import OpenAIClient
from customer_complaint_agent.shared.model import (
    ModelCallBudget,
    ModelClientRegistration,
    ModelClientRegistry,
)
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
        EvaluateRefundPolicyTool.name,
    ),
    "compliment_agent": (
        GetEmailTool.name,
        VerifyDamagedProductTool.name,
    ),
}


def run_email_handler(email_id: str) -> RunResult:
    """Run the email handling runtime with production dependencies."""
    settings = _create_settings()
    model_client_registry = _create_model_client_registry(settings)
    agent_registry = AgentRegistry()

    return run_email_handler_with_dependencies(
        email_id,
        model_client_registry,
        agent_registry,
    )


def run_email_handler_with_dependencies(
    email_id: str,
    model_client_registry: ModelClientRegistry,
    agent_registry: AgentRegistry,
) -> RunResult:
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
    tool_registry = _create_tool_registry(route.agent_name, store)

    agent = agent_registry.get(route.agent_name)

    if agent is None:
        return RunResult(
            run_id=goal_state.goal_id,
            status=RunStatus.FAILED,
            completion_type=None,
            details={"reason_code": "agent_not_found"},
        )

    agent_harness = AgentHarness()
    return agent_harness.run_agent_goal(
        agent,
        goal_state,
        tool_registry,
        model_client_registry,
        settings,
    )


def _create_model_client_registry(settings: Settings) -> ModelClientRegistry:
    return ModelClientRegistry(
        model_call_budget=ModelCallBudget(
            max_paid_model_calls=settings.max_paid_model_calls,
        ),
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
        EvaluateRefundPolicyTool.name: EvaluateRefundPolicyTool(),
    }

    tools: list[Tool] = []

    for tool_name in _AGENT_TOOL_NAMES.get(agent_name, ()):
        tool = available_tools.get(tool_name)

        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not available.")

        tools.append(tool)

    registry_tools = tuple(tools)
    return ToolRegistry(tools=registry_tools)


def _create_settings() -> Settings:
    return Settings(
        attachments_directory=Path("data/attachments"),
        max_agent_turns=10,
        max_paid_model_calls=10,
    )

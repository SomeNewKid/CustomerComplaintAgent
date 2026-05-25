"""Runtime entry point for handling customer emails."""

from customer_complaint_agent.domain.store import Store
from customer_complaint_agent.harness.runner import AgentHarness, RunResult, RunStatus
from customer_complaint_agent.shared.model import ModelClientRegistry

from .agent_registry import AgentRegistry
from .agent_router import AgentRouter
from .goal_state import create_email_goal_state
from .model_clients import create_model_client_registry
from .settings import create_settings
from .tool_registry import create_tool_registry


def run_email_handler(email_id: str) -> RunResult:
    """Run the email handling runtime with production dependencies."""
    settings = create_settings()
    model_client_registry = create_model_client_registry(settings)
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
    settings = create_settings()
    email = store.get_email(email_id)
    goal_state = create_email_goal_state(email_id)

    if email is None:
        return RunResult(
            run_id=goal_state.goal_id,
            status=RunStatus.FAILED,
            completion_type=None,
            details={"reason_code": "email_not_found"},
        )

    router = AgentRouter()
    route = router.route(email)
    tool_registry = create_tool_registry(route.agent_name, store)

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

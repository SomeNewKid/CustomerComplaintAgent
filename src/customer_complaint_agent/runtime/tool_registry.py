"""Runtime tool registry creation."""

from customer_complaint_agent.domain.store import Store
from customer_complaint_agent.domain.tools import (
    EvaluateRefundPolicyTool,
    GetCustomerTool,
    GetEmailTool,
    GetOrderTool,
    GetProductTool,
    VerifyDamagedProductTool,
)
from customer_complaint_agent.shared.tool import Tool, ToolRegistry

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


def create_tool_registry(agent_name: str, store: Store) -> ToolRegistry:
    """Create the tool registry available to one routed agent."""
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

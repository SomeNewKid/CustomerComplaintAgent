"""Order tools."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from ..store import Store


class GetOrderTool:
    """Tool that retrieves an order by ID."""

    name = "get_order"
    description = "Retrieve an order by order_id."
    arguments = (
        ToolArgument(
            name="order_id",
            argument_type="string",
            description="The identifier of an order.",
        ),
    )

    def __init__(self, store: Store) -> None:
        """Create the tool with its data store."""
        self._store = store

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        order_id = str(tool_request["order_id"])
        order = self._store.get_order(order_id)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"order": order},
        )

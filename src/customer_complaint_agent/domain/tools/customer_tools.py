"""Customer tools."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from ..store import Store


class GetCustomerTool:
    """Tool that retrieves a customer by ID."""

    name = "get_customer"
    description = "Retrieve a customer by customer_id."
    arguments = (
        ToolArgument(
            name="customer_id",
            argument_type="string",
            description="The identifier of a customer.",
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
        customer_id = str(tool_request["customer_id"])
        customer = self._store.get_customer(customer_id)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"customer": customer},
        )

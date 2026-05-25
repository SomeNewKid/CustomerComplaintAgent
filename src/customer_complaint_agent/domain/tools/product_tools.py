"""Product tools."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from ..store import Store


class GetProductTool:
    """Tool that retrieves a product by ID."""

    name = "get_product"
    description = "Retrieve a product by product_id."
    arguments = (
        ToolArgument(
            name="product_id",
            argument_type="string",
            description="The identifier of a product.",
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
        product_id = str(tool_request["product_id"])
        product = self._store.get_product(product_id)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"product": product},
        )

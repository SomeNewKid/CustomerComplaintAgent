"""Email tools."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from ..store import Store


class GetEmailTool:
    """Tool that retrieves an email by ID."""

    name = "get_email"
    description = "Retrieve an email by email_id."
    arguments = (
        ToolArgument(
            name="email_id",
            argument_type="string",
            description="The identifier of an email.",
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
        email_id = str(tool_request["email_id"])
        email = self._store.get_email(email_id)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"email": email},
        )

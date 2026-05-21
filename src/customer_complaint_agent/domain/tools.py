"""Domain tools available to configured agents."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolRequest, ToolRuntime

from .store import Store


class GetEmailTool:
    """Tool that retrieves an email by ID."""

    name = "get_email"

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


class GetOrderTool:
    """Tool that retrieves an order by ID."""

    name = "get_order"

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


class GetProductTool:
    """Tool that retrieves a product by ID."""

    name = "get_product"

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


class GetCustomerTool:
    """Tool that retrieves a customer by ID."""

    name = "get_customer"

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


class VerifyDamagedProductTool:
    """Tool that verifies whether an attachment shows product damage."""

    name = "verify_damaged_product"

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        filename = str(tool_request["filename"])
        attachment_path = tool_runtime.settings.attachments_directory / filename
        attachment_exists = attachment_path.is_file()
        damage_verified = attachment_exists and self._filename_indicates_damage(
            filename,
        )

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={
                "filename": filename,
                "attachment_exists": attachment_exists,
                "damage_verified": damage_verified,
            },
        )

    def _filename_indicates_damage(self, filename: str) -> bool:
        normalized_filename = filename.casefold()
        return "broken" in normalized_filename and "unbroken" not in normalized_filename

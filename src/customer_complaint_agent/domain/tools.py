"""Domain tools available to configured agents."""

from pathlib import Path

from customer_complaint_agent.shared.model import ModelRequest, ModelResponse
from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from .refunds.refund_policy import RefundFacts, RefundPolicy
from .store import Store


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


class VerifyDamagedProductTool:
    """Tool that verifies whether an attachment shows product damage."""

    name = "verify_damaged_product"
    description = "Verify whether an attachment image shows product damage."
    arguments = (
        ToolArgument(
            name="filename",
            argument_type="string",
            description="The filename of the product photo attachment.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        filename = str(tool_request["filename"])
        attachment_path = tool_runtime.settings.attachments_directory / filename
        attachment_exists = attachment_path.is_file()

        if not attachment_exists:
            return ToolResult(
                tool_name=self.name,
                arguments=tool_request,
                data={
                    "filename": filename,
                    "attachment_exists": False,
                    "damage_verified": False,
                    "confidence": 0.0,
                    "supporting_text": "Attachment file was not found.",
                },
            )

        vision_client = tool_runtime.model_client_registry.get_vision_client()

        if vision_client is None:
            return ToolResult(
                tool_name=self.name,
                arguments=tool_request,
                data={
                    "filename": filename,
                    "attachment_exists": True,
                    "damage_verified": None,
                    "confidence": 0.0,
                    "supporting_text": "No vision model client was available.",
                },
            )

        model_request = self._create_model_request(attachment_path)
        model_response = vision_client.complete(model_request)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={
                "filename": filename,
                "attachment_exists": True,
                "damage_verified": self._damage_verified(model_response),
                "confidence": self._confidence(model_response),
                "supporting_text": self._supporting_text(model_response),
            },
        )

    def _create_model_request(self, attachment_path: Path) -> ModelRequest:
        return ModelRequest(
            system_prompt=(
                "You inspect customer email attachment photos for product damage. "
                "Return only structured JSON that matches the requested schema."
            ),
            user_prompt=(
                "Determine whether the attached image shows a damaged product. "
                "Set damage_verified to true only when visible product damage is "
                "clear from the image."
            ),
            input_data={},
            response_schema={
                "type": "object",
                "properties": {
                    "damage_verified": {"type": "boolean"},
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "supporting_text": {"type": "string"},
                },
                "required": [
                    "damage_verified",
                    "confidence",
                    "supporting_text",
                ],
                "additionalProperties": False,
            },
            response_schema_name="damage_verification",
            image_paths=(attachment_path,),
        )

    def _damage_verified(self, response: ModelResponse) -> bool:
        return bool(response.data["damage_verified"])

    def _confidence(self, response: ModelResponse) -> float:
        confidence = response.data["confidence"]

        if isinstance(confidence, int | float):
            return float(confidence)

        return 0.0

    def _supporting_text(self, response: ModelResponse) -> str:
        return str(response.data["supporting_text"])


class EvaluateRefundPolicyTool:
    """Tool that evaluates refund policy from established facts."""

    name = "evaluate_refund_policy"
    description = "Evaluate refund eligibility from refund policy facts."
    arguments = (
        ToolArgument(
            name="already_refunded",
            argument_type="boolean",
            description="Whether the order has already been refunded.",
        ),
        ToolArgument(
            name="product_price",
            argument_type="number",
            description="The price of the product associated with the order.",
        ),
        ToolArgument(
            name="damage_verified",
            argument_type="boolean",
            description="Whether product damage has been verified.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        product_price_value = tool_request["product_price"]
        product_price_text = str(product_price_value)
        product_price = float(product_price_text)
        refund_facts = RefundFacts(
            already_refunded=bool(tool_request["already_refunded"]),
            product_price=product_price,
            damage_verified=bool(tool_request["damage_verified"]),
        )
        refund_policy = RefundPolicy()
        refund_decision = refund_policy.evaluate(refund_facts)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"refund_decision": refund_decision},
        )

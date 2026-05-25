"""Refund policy tools."""

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime

from ..refunds.refund_policy import RefundFacts, RefundPolicy


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

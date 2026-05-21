"""Deterministic complaint agent placeholder."""

from customer_complaint_agent.domain.entities import Email, Order, Product
from customer_complaint_agent.domain.reducers import (
    EmailEntityReducer,
    OrderEntityReducer,
    ProductEntityReducer,
)
from customer_complaint_agent.domain.refunds.refund_policy import (
    RefundFacts,
    RefundPolicy,
)
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.state import GoalState
from customer_complaint_agent.shared.validation import ValidationRule


class ComplaintAgent:
    """Agent responsible for complaint email workflows."""

    name = "complaint_agent"

    def decide(self, request: AgentRequest) -> AgentDecision:
        """Return the next deterministic complaint handling decision."""
        email = self._get_email(request.goal_state)

        if email is None:
            return ActionDecision(
                tool_name="get_email",
                arguments={"email_id": request.goal_state.root_entity.entity_id},
                reason="Need to inspect the customer complaint email.",
            )

        if email.order_id is None:
            return self._blocked_decision("missing_order_id")

        order = self._get_order(request.goal_state)

        if order is None:
            return ActionDecision(
                tool_name="get_order",
                arguments={"order_id": email.order_id},
                reason="Need to inspect the order associated with the complaint.",
            )

        product = self._get_product(request.goal_state)

        if product is None:
            return ActionDecision(
                tool_name="get_product",
                arguments={"product_id": order.product_id},
                reason="Need to inspect the product associated with the order.",
            )

        damage_verified = self._get_damage_verified(request.goal_state)

        if damage_verified is None:
            if email.attachment is None:
                return self._blocked_decision("missing_attachment")

            return ActionDecision(
                tool_name="verify_damaged_product",
                arguments={"filename": email.attachment},
                reason="Need to verify whether the attachment shows damage.",
            )

        refund_decision = RefundPolicy().evaluate(
            RefundFacts(
                already_refunded=order.refunded,
                product_price=product.price,
                damage_verified=damage_verified,
            )
        )

        return FinalDecision(
            completion_type="done",
            details={
                "refund_decision": refund_decision.decision_type,
                "reason_code": refund_decision.reason_code,
            },
            reason="Evaluated the complaint against the refund policy.",
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        """Return validation rules specific to this agent."""
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        """Return reducers used by this agent to update goal state."""
        return [
            EmailEntityReducer(),
            OrderEntityReducer(),
            ProductEntityReducer(),
        ]

    def _get_email(self, goal_state: GoalState) -> Email | None:
        for tool_result in goal_state.tool_results:
            email = tool_result.data.get("email")

            if isinstance(email, Email):
                return email

        return None

    def _get_order(self, goal_state: GoalState) -> Order | None:
        for tool_result in goal_state.tool_results:
            order = tool_result.data.get("order")

            if isinstance(order, Order):
                return order

        return None

    def _get_product(self, goal_state: GoalState) -> Product | None:
        for tool_result in goal_state.tool_results:
            product = tool_result.data.get("product")

            if isinstance(product, Product):
                return product

        return None

    def _get_damage_verified(self, goal_state: GoalState) -> bool | None:
        for tool_result in goal_state.tool_results:
            if tool_result.tool_name != "verify_damaged_product":
                continue

            damage_verified = tool_result.data.get("damage_verified")

            if isinstance(damage_verified, bool):
                return damage_verified

        return None

    def _blocked_decision(self, reason_code: str) -> FinalDecision:
        return FinalDecision(
            completion_type="blocked",
            details={"reason_code": reason_code},
            reason="Complaint handling could not continue.",
        )

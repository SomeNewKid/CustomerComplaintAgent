"""Domain reducers for updating goal state from tool results."""

from customer_complaint_agent.shared.state import EntityRef, GoalState, ToolResult

from .entities import Customer, Email, Order, Product


class CustomerEntityReducer:
    """Reducer that records customer entity references."""

    def apply(
        self,
        goal_state: GoalState,
        tool_result: ToolResult,
    ) -> None:
        """Apply customer state updates from a tool result."""
        customer = tool_result.data.get("customer")

        if not isinstance(customer, Customer):
            return

        goal_state.set_entity_reference(
            EntityRef(entity_type="customer", entity_id=customer.customer_id)
        )


class EmailEntityReducer:
    """Reducer that records email entity references."""

    def apply(
        self,
        goal_state: GoalState,
        tool_result: ToolResult,
    ) -> None:
        """Apply email state updates from a tool result."""
        email = tool_result.data.get("email")

        if not isinstance(email, Email):
            return

        goal_state.set_entity_reference(
            EntityRef(entity_type="email", entity_id=email.email_id)
        )


class OrderEntityReducer:
    """Reducer that records order entity references."""

    def apply(
        self,
        goal_state: GoalState,
        tool_result: ToolResult,
    ) -> None:
        """Apply order state updates from a tool result."""
        order = tool_result.data.get("order")

        if not isinstance(order, Order):
            return

        goal_state.set_entity_reference(
            EntityRef(entity_type="order", entity_id=order.order_id)
        )


class ProductEntityReducer:
    """Reducer that records product entity references."""

    def apply(
        self,
        goal_state: GoalState,
        tool_result: ToolResult,
    ) -> None:
        """Apply product state updates from a tool result."""
        product = tool_result.data.get("product")

        if not isinstance(product, Product):
            return

        goal_state.set_entity_reference(
            EntityRef(entity_type="product", entity_id=product.product_id)
        )

import pytest

from customer_complaint_agent.domain.entities import Customer, Email, Order, Product
from customer_complaint_agent.domain.reducers import (
    CustomerEntityReducer,
    EmailEntityReducer,
    OrderEntityReducer,
    ProductEntityReducer,
)
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalState,
    GoalStatus,
    ToolResult,
)


def test_customer_entity_reducer_adds_missing_entity_reference() -> None:
    goal_state = _goal_state()

    CustomerEntityReducer().apply(goal_state, _customer_tool_result("C001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="customer", entity_id="C001"),
    ]


def test_customer_entity_reducer_leaves_matching_entity_reference_unchanged() -> None:
    goal_state = _goal_state([EntityRef(entity_type="customer", entity_id="C001")])

    CustomerEntityReducer().apply(goal_state, _customer_tool_result("C001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="customer", entity_id="C001"),
    ]


def test_customer_entity_reducer_raises_error_for_conflicting_entity_reference() -> (
    None
):
    goal_state = _goal_state([EntityRef(entity_type="customer", entity_id="C001")])

    with pytest.raises(
        RuntimeError,
        match="Conflicting entity reference for customer.",
    ):
        CustomerEntityReducer().apply(goal_state, _customer_tool_result("C002"))


def test_email_entity_reducer_adds_missing_entity_reference() -> None:
    goal_state = _goal_state([])

    EmailEntityReducer().apply(goal_state, _email_tool_result("E001"))

    assert goal_state.entities == [EntityRef(entity_type="email", entity_id="E001")]


def test_email_entity_reducer_leaves_matching_entity_reference_unchanged() -> None:
    goal_state = _goal_state()

    EmailEntityReducer().apply(goal_state, _email_tool_result("E001"))

    assert goal_state.entities == [EntityRef(entity_type="email", entity_id="E001")]


def test_email_entity_reducer_raises_error_for_conflicting_entity_reference() -> None:
    goal_state = _goal_state()

    with pytest.raises(
        RuntimeError,
        match="Conflicting entity reference for email.",
    ):
        EmailEntityReducer().apply(goal_state, _email_tool_result("E002"))


def test_order_entity_reducer_adds_missing_entity_reference() -> None:
    goal_state = _goal_state()

    OrderEntityReducer().apply(goal_state, _order_tool_result("O001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="order", entity_id="O001"),
    ]


def test_order_entity_reducer_leaves_matching_entity_reference_unchanged() -> None:
    goal_state = _goal_state([EntityRef(entity_type="order", entity_id="O001")])

    OrderEntityReducer().apply(goal_state, _order_tool_result("O001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="order", entity_id="O001"),
    ]


def test_order_entity_reducer_raises_error_for_conflicting_entity_reference() -> None:
    goal_state = _goal_state([EntityRef(entity_type="order", entity_id="O001")])

    with pytest.raises(
        RuntimeError,
        match="Conflicting entity reference for order.",
    ):
        OrderEntityReducer().apply(goal_state, _order_tool_result("O002"))


def test_product_entity_reducer_adds_missing_entity_reference() -> None:
    goal_state = _goal_state()

    ProductEntityReducer().apply(goal_state, _product_tool_result("P001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="product", entity_id="P001"),
    ]


def test_product_entity_reducer_leaves_matching_entity_reference_unchanged() -> None:
    goal_state = _goal_state([EntityRef(entity_type="product", entity_id="P001")])

    ProductEntityReducer().apply(goal_state, _product_tool_result("P001"))

    assert goal_state.entities == [
        EntityRef(entity_type="email", entity_id="E001"),
        EntityRef(entity_type="product", entity_id="P001"),
    ]


def test_product_entity_reducer_raises_error_for_conflicting_entity_reference() -> None:
    goal_state = _goal_state([EntityRef(entity_type="product", entity_id="P001")])

    with pytest.raises(
        RuntimeError,
        match="Conflicting entity reference for product.",
    ):
        ProductEntityReducer().apply(goal_state, _product_tool_result("P002"))


def _goal_state(entities: list[EntityRef] | None = None) -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity, *(entities or [])],
        tool_results=[],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )


def _customer_tool_result(customer_id: str) -> ToolResult:
    return ToolResult(
        tool_name="get_customer",
        arguments={"customer_id": customer_id},
        data={
            "customer": Customer(
                customer_id=customer_id,
                name="Example Customer",
                email="customer@example.com",
            )
        },
    )


def _email_tool_result(email_id: str) -> ToolResult:
    return ToolResult(
        tool_name="get_email",
        arguments={"email_id": email_id},
        data={
            "email": Email(
                email_id=email_id,
                customer_id="C001",
                order_id="O001",
                message="Example message.",
                attachment=None,
                status="open",
            )
        },
    )


def _order_tool_result(order_id: str) -> ToolResult:
    return ToolResult(
        tool_name="get_order",
        arguments={"order_id": order_id},
        data={
            "order": Order(
                order_id=order_id,
                customer_id="C001",
                product_id="P001",
                order_date="2026-05-01",
                promised_delivery_date="2026-05-03",
                actual_delivery_date="2026-05-03",
                status="delivered",
                refunded=False,
            )
        },
    )


def _product_tool_result(product_id: str) -> ToolResult:
    return ToolResult(
        tool_name="get_product",
        arguments={"product_id": product_id},
        data={
            "product": Product(
                product_id=product_id,
                name="Example Product",
                category="example",
                price=10.0,
            )
        },
    )

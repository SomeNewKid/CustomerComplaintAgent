from customer_complaint_agent.agents.deterministic_complaint_agent import (
    DeterministicComplaintAgent,
)
from customer_complaint_agent.domain.entities import Email, Order, Product
from customer_complaint_agent.domain.refunds.refund_policy import RefundDecision
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalState,
    GoalStatus,
    ToolResult,
)
from customer_complaint_agent.shared.tool import ToolRegistry


def test_deterministic_complaint_agent_blocks_when_email_has_no_order_id() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E101",
                            customer_id="C001",
                            order_id=None,
                            message="My item arrived damaged.",
                            attachment="broken-mug.jpg",
                            status="open",
                        )
                    )
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    _assert_blocked(decision, "missing_order_id")


def test_deterministic_complaint_agent_blocks_when_email_is_not_found() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    ToolResult(
                        tool_name="get_email",
                        arguments={"email_id": "E001"},
                        data={"email": None},
                    )
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    _assert_blocked(decision, "email_not_found")


def test_deterministic_complaint_agent_blocks_when_order_is_not_found() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E102",
                            customer_id="C001",
                            order_id="O999",
                            message="My item arrived damaged.",
                            attachment="broken-mug.jpg",
                            status="open",
                        )
                    ),
                    ToolResult(
                        tool_name="get_order",
                        arguments={"order_id": "O999"},
                        data={"order": None},
                    ),
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    _assert_blocked(decision, "order_not_found")


def test_deterministic_complaint_agent_blocks_when_product_is_not_found() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E105",
                            customer_id="C001",
                            order_id="O001",
                            message="My item arrived damaged.",
                            attachment="broken-mug.jpg",
                            status="open",
                        )
                    ),
                    ToolResult(
                        tool_name="get_order",
                        arguments={"order_id": "O001"},
                        data={
                            "order": Order(
                                order_id="O001",
                                customer_id="C001",
                                product_id="P999",
                                order_date="2026-05-01",
                                promised_delivery_date="2026-05-05",
                                actual_delivery_date="2026-05-15",
                                status="delivered",
                                refunded=False,
                            )
                        },
                    ),
                    ToolResult(
                        tool_name="get_product",
                        arguments={"product_id": "P999"},
                        data={"product": None},
                    ),
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    _assert_blocked(decision, "product_not_found")


def test_deterministic_complaint_agent_blocks_when_email_has_no_attachment() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E103",
                            customer_id="C001",
                            order_id="O001",
                            message="My item arrived damaged.",
                            attachment=None,
                            status="open",
                        )
                    ),
                    _order_tool_result(),
                    _product_tool_result(),
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    _assert_blocked(decision, "missing_attachment")


def test_deterministic_complaint_agent_requests_refund_policy_evaluation() -> None:
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E104",
                            customer_id="C001",
                            order_id="O001",
                            message="My item arrived damaged.",
                            attachment="missing.jpg",
                            status="open",
                        )
                    ),
                    _order_tool_result(),
                    _product_tool_result(),
                    ToolResult(
                        tool_name="verify_damaged_product",
                        arguments={"filename": "missing.jpg"},
                        data={
                            "filename": "missing.jpg",
                            "attachment_exists": False,
                            "damage_verified": False,
                        },
                    ),
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    assert isinstance(decision, ActionDecision)
    assert decision.tool_name == "evaluate_refund_policy"
    assert decision.arguments == {
        "already_refunded": False,
        "product_price": 12.0,
        "damage_verified": False,
    }


def test_deterministic_complaint_agent_finishes_from_refund_policy_tool_result() -> (
    None
):
    decision = DeterministicComplaintAgent().decide(
        AgentRequest(
            goal_state=_goal_state(
                [
                    _email_tool_result(
                        Email(
                            email_id="E104",
                            customer_id="C001",
                            order_id="O001",
                            message="My item arrived damaged.",
                            attachment="missing.jpg",
                            status="open",
                        )
                    ),
                    _order_tool_result(),
                    _product_tool_result(),
                    ToolResult(
                        tool_name="verify_damaged_product",
                        arguments={"filename": "missing.jpg"},
                        data={
                            "filename": "missing.jpg",
                            "attachment_exists": False,
                            "damage_verified": False,
                        },
                    ),
                    _refund_policy_tool_result(
                        already_refunded=False,
                        product_price=12.0,
                        damage_verified=False,
                        decision_type="decline",
                        reason_code="damage_not_verified",
                    ),
                ]
            ),
            tool_registry=ToolRegistry(tools=()),
        )
    )

    assert isinstance(decision, FinalDecision)
    assert decision.completion_type == "done"
    assert decision.details == {
        "refund_decision": "decline",
        "reason_code": "damage_not_verified",
    }


def _assert_blocked(decision: object, reason_code: str) -> None:
    assert isinstance(decision, FinalDecision)
    assert decision.completion_type == "blocked"
    assert decision.details == {"reason_code": reason_code}


def _goal_state(tool_results: list[ToolResult]) -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=tool_results,
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )


def _email_tool_result(email: Email) -> ToolResult:
    return ToolResult(
        tool_name="get_email",
        arguments={"email_id": email.email_id},
        data={"email": email},
    )


def _order_tool_result() -> ToolResult:
    return ToolResult(
        tool_name="get_order",
        arguments={"order_id": "O001"},
        data={
            "order": Order(
                order_id="O001",
                customer_id="C001",
                product_id="P001",
                order_date="2026-05-01",
                promised_delivery_date="2026-05-05",
                actual_delivery_date="2026-05-15",
                status="delivered",
                refunded=False,
            )
        },
    )


def _product_tool_result() -> ToolResult:
    return ToolResult(
        tool_name="get_product",
        arguments={"product_id": "P001"},
        data={
            "product": Product(
                product_id="P001",
                name="Cheap Mug",
                category="homewares",
                price=12.0,
            )
        },
    )


def _refund_policy_tool_result(
    already_refunded: bool,
    product_price: float,
    damage_verified: bool,
    decision_type: str,
    reason_code: str,
) -> ToolResult:
    return ToolResult(
        tool_name="evaluate_refund_policy",
        arguments={
            "already_refunded": already_refunded,
            "product_price": product_price,
            "damage_verified": damage_verified,
        },
        data={
            "refund_decision": RefundDecision(
                decision_type=decision_type,
                reason_code=reason_code,
            )
        },
    )

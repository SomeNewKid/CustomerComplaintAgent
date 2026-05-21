from customer_complaint_agent.domain.refunds.refund_policy import (
    RefundDecision,
    RefundFacts,
    RefundPolicy,
)


def test_refund_policy_declines_refunded_verified_below_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=True,
        product_price=49.99,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_declines_refunded_verified_at_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=True,
        product_price=50.0,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_declines_refunded_verified_above_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=True,
        product_price=50.01,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_declines_refunded_not_verified_below_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=False,
        product_price=49.99,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_declines_refunded_not_verified_at_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=False,
        product_price=50.0,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_declines_refunded_not_verified_above_threshold() -> None:
    decision = _evaluate(
        already_refunded=True,
        damage_verified=False,
        product_price=50.01,
    )

    _assert_decision(decision, "decline", "already_refunded")


def test_refund_policy_refunds_not_refunded_verified_below_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=True,
        product_price=49.99,
    )

    _assert_decision(decision, "refund", "damaged_cheap_item")


def test_refund_policy_refunds_not_refunded_verified_at_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=True,
        product_price=50.0,
    )

    _assert_decision(decision, "refund", "damaged_cheap_item")


def test_refund_policy_escalates_not_refunded_verified_above_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=True,
        product_price=50.01,
    )

    _assert_decision(decision, "escalate", "damaged_expensive_item")


def test_refund_policy_declines_not_refunded_not_verified_below_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=False,
        product_price=49.99,
    )

    _assert_decision(decision, "decline", "damage_not_verified")


def test_refund_policy_declines_not_refunded_not_verified_at_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=False,
        product_price=50.0,
    )

    _assert_decision(decision, "decline", "damage_not_verified")


def test_refund_policy_declines_not_refunded_not_verified_above_threshold() -> None:
    decision = _evaluate(
        already_refunded=False,
        damage_verified=False,
        product_price=50.01,
    )

    _assert_decision(decision, "decline", "damage_not_verified")


def _evaluate(
    already_refunded: bool,
    damage_verified: bool,
    product_price: float,
) -> RefundDecision:
    return RefundPolicy().evaluate(
        RefundFacts(
            already_refunded=already_refunded,
            damage_verified=damage_verified,
            product_price=product_price,
        )
    )


def _assert_decision(
    decision: RefundDecision,
    decision_type: str,
    reason_code: str,
) -> None:
    assert decision.decision_type == decision_type
    assert decision.reason_code == reason_code

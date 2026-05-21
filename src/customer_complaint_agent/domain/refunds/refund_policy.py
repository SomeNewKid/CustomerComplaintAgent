"""Refund policy evaluation."""

from dataclasses import dataclass

_MAX_AUTOMATIC_REFUND_PRICE = 50.0


@dataclass(frozen=True)
class RefundFacts:
    """Facts required to evaluate refund eligibility."""

    already_refunded: bool
    product_price: float
    damage_verified: bool


@dataclass(frozen=True)
class RefundDecision:
    """Decision produced by the refund policy."""

    decision_type: str
    reason_code: str


class RefundPolicy:
    """Deterministic refund policy evaluator."""

    def evaluate(self, facts: RefundFacts) -> RefundDecision:
        """Evaluate refund eligibility from structured facts."""
        if facts.already_refunded:
            return RefundDecision(
                decision_type="decline",
                reason_code="already_refunded",
            )

        if not facts.damage_verified:
            return RefundDecision(
                decision_type="decline",
                reason_code="damage_not_verified",
            )

        if facts.product_price <= _MAX_AUTOMATIC_REFUND_PRICE:
            return RefundDecision(
                decision_type="refund",
                reason_code="damaged_cheap_item",
            )

        return RefundDecision(
            decision_type="escalate",
            reason_code="damaged_expensive_item",
        )

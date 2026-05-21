"""Validation behavior used by the agent harness."""

from customer_complaint_agent.shared.agent import AgentDecision
from customer_complaint_agent.shared.state import GoalState
from customer_complaint_agent.shared.validation import (
    ValidationError,
    ValidationResult,
    ValidationRule,
)


def validate_decision(
    decision: AgentDecision,
    goal_state: GoalState,
    rules: list[ValidationRule],
) -> ValidationResult:
    """Validate an agent decision using the provided rules."""
    errors: list[ValidationError] = []
    for rule in rules:
        errors.extend(rule.validate(decision, goal_state))

    return ValidationResult(errors=errors)

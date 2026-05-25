"""Validation rules derived from agent skills."""

from customer_complaint_agent.shared.agent import AgentDecision
from customer_complaint_agent.shared.state import GoalState
from customer_complaint_agent.shared.validation import ValidationError

from .skill import AgentSkill


class SkillStateUpdateRule:
    """Validate state update vocabulary against an agent skill."""

    def __init__(self, skill: AgentSkill) -> None:
        """Create the rule for one agent skill."""
        self._skill = skill

    def validate(
        self,
        decision: AgentDecision,
        goal_state: GoalState,
    ) -> list[ValidationError]:
        """Return validation errors for invalid skill vocabulary."""
        errors: list[ValidationError] = []

        for state_update in decision.state_updates:
            if state_update.operation == "add_claim":
                claim_error = self._validate_claim_type(state_update.arguments)

                if claim_error is not None:
                    errors.append(claim_error)
            elif state_update.operation == "add_fact":
                fact_error = self._validate_fact_type(state_update.arguments)

                if fact_error is not None:
                    errors.append(fact_error)

        return errors

    def _validate_claim_type(
        self,
        arguments: dict[str, object],
    ) -> ValidationError | None:
        claim_type = arguments.get("claim_type")

        if not isinstance(claim_type, str):
            return None

        if claim_type in self._skill.claim_types:
            return None

        return ValidationError(
            code="invalid_claim_type",
            message=f"Claim type '{claim_type}' is not valid for this agent skill.",
        )

    def _validate_fact_type(
        self,
        arguments: dict[str, object],
    ) -> ValidationError | None:
        fact_type = arguments.get("fact_type")

        if not isinstance(fact_type, str):
            return None

        if fact_type in self._skill.fact_types:
            return None

        return ValidationError(
            code="invalid_fact_type",
            message=f"Fact type '{fact_type}' is not valid for this agent skill.",
        )

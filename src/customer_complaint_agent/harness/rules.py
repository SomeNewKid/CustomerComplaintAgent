"""Harness validation rules."""

from typing import cast

from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentDecision,
    FinalDecision,
)
from customer_complaint_agent.shared.state import GoalState
from customer_complaint_agent.shared.tool import ToolRegistry
from customer_complaint_agent.shared.validation import (
    ValidationError,
    ValidationRule,
)

COMPLETION_TYPES = {
    "done": "The agent has completed the goal.",
    "blocked": (
        "The agent could not complete the goal because required information or "
        "conditions were missing."
    ),
    "handoff_request": "Another agent should continue the goal.",
    "approval_request": "Human approval is required before continuing.",
}

STATE_UPDATE_OPERATIONS = {
    "add_claim",
    "add_fact",
    "add_output",
}


class CompletionTypeRule:
    """Validate final decision completion types."""

    def validate(
        self,
        decision: AgentDecision,
        goal_state: GoalState,
    ) -> list[ValidationError]:
        """Return validation errors for an invalid completion type."""
        if not isinstance(decision, FinalDecision):
            return []

        if not decision.completion_type:
            return [
                ValidationError(
                    code="missing_completion_type",
                    message="Final decisions must include a completion type.",
                )
            ]

        if decision.completion_type in COMPLETION_TYPES:
            return []

        return [
            ValidationError(
                code="invalid_completion_type",
                message=(f"Completion type '{decision.completion_type}' is not valid."),
            )
        ]


class ToolNameRule:
    """Validate action decision tool names."""

    def validate(
        self,
        decision: AgentDecision,
        goal_state: GoalState,
    ) -> list[ValidationError]:
        """Return validation errors for a missing tool name."""
        if not isinstance(decision, ActionDecision):
            return []

        if decision.tool_name:
            return []

        return [
            ValidationError(
                code="missing_tool_name",
                message="Action decisions must include a tool name.",
            )
        ]


class RegisteredToolRule:
    """Validate action decision tool names against a tool registry."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """Create the rule with the registry available for this run."""
        self._tool_registry = tool_registry

    def validate(
        self,
        decision: AgentDecision,
        goal_state: GoalState,
    ) -> list[ValidationError]:
        """Return validation errors for an unregistered tool name."""
        if not isinstance(decision, ActionDecision):
            return []

        if not decision.tool_name:
            return []

        if self._tool_registry.get(decision.tool_name) is not None:
            return []

        return [
            ValidationError(
                code="unknown_tool",
                message=f"Tool '{decision.tool_name}' is not registered.",
            )
        ]


class StateUpdateShapeRule:
    """Validate state update operation and argument shapes."""

    def validate(
        self,
        decision: AgentDecision,
        goal_state: GoalState,
    ) -> list[ValidationError]:
        """Return validation errors for invalid state updates."""
        errors: list[ValidationError] = []

        for state_update in decision.state_updates:
            if state_update.operation not in STATE_UPDATE_OPERATIONS:
                errors.append(
                    ValidationError(
                        code="unknown_state_update_operation",
                        message=(
                            f"State update operation "
                            f"'{state_update.operation}' is not valid."
                        ),
                    )
                )
                continue

            if state_update.operation == "add_claim":
                errors.extend(self._validate_add_claim(state_update.arguments))
            elif state_update.operation == "add_fact":
                errors.extend(self._validate_add_fact(state_update.arguments))
            elif state_update.operation == "add_output":
                errors.extend(self._validate_add_output(state_update.arguments))

        return errors

    def _validate_add_claim(
        self,
        arguments: dict[str, object],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not self._has_non_empty_string(arguments, "claim_type"):
            errors.append(
                ValidationError(
                    code="missing_claim_type",
                    message="State update add_claim must include a claim type.",
                )
            )

        if not self._has_valid_source(arguments):
            errors.append(
                ValidationError(
                    code="invalid_source",
                    message=(
                        "State update source must include entity_type and entity_id."
                    ),
                )
            )

        if not self._has_non_empty_string(arguments, "supporting_text"):
            errors.append(
                ValidationError(
                    code="missing_supporting_text",
                    message="State update add_claim must include supporting text.",
                )
            )

        return errors

    def _validate_add_fact(
        self,
        arguments: dict[str, object],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not self._has_non_empty_string(arguments, "fact_type"):
            errors.append(
                ValidationError(
                    code="missing_fact_type",
                    message="State update add_fact must include a fact type.",
                )
            )

        if not self._has_valid_source(arguments):
            errors.append(
                ValidationError(
                    code="invalid_source",
                    message=(
                        "State update source must include entity_type and entity_id."
                    ),
                )
            )

        if not self._has_dict(arguments, "data"):
            errors.append(
                ValidationError(
                    code="missing_data",
                    message="State update add_fact must include data.",
                )
            )

        return errors

    def _validate_add_output(
        self,
        arguments: dict[str, object],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not self._has_non_empty_string(arguments, "output_type"):
            errors.append(
                ValidationError(
                    code="missing_output_type",
                    message="State update add_output must include an output type.",
                )
            )

        if not self._has_dict(arguments, "data"):
            errors.append(
                ValidationError(
                    code="missing_data",
                    message="State update add_output must include data.",
                )
            )

        return errors

    def _has_dict(
        self,
        arguments: dict[str, object],
        key: str,
    ) -> bool:
        value = arguments.get(key)
        return isinstance(value, dict)

    def _has_non_empty_string(
        self,
        arguments: dict[str, object],
        key: str,
    ) -> bool:
        value = arguments.get(key)
        return isinstance(value, str) and bool(value)

    def _has_valid_source(self, arguments: dict[str, object]) -> bool:
        source = arguments.get("source")

        if not isinstance(source, dict):
            return False

        source_arguments = cast(dict[str, object], source)
        entity_type = source_arguments.get("entity_type")
        entity_id = source_arguments.get("entity_id")
        return (
            isinstance(entity_type, str)
            and bool(entity_type)
            and isinstance(entity_id, str)
            and bool(entity_id)
        )


HARNESS_VALIDATION_RULES: list[ValidationRule] = [
    CompletionTypeRule(),
    ToolNameRule(),
    StateUpdateShapeRule(),
]

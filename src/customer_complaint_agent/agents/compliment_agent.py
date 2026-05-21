"""Deterministic compliment agent placeholder."""

from customer_complaint_agent.shared.agent import AgentRequest, FinalDecision
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.validation import ValidationRule


class ComplimentAgent:
    """Agent responsible for compliment email workflows."""

    name = "compliment_agent"

    def decide(self, request: AgentRequest) -> FinalDecision:
        """Return an inert decision until compliment handling is implemented."""
        entity_id = request.goal_state.root_entity.entity_id
        reason = f"Compliment handling is not implemented for {entity_id}."
        return FinalDecision(
            completion_type="not_implemented",
            details={"agent": self.name},
            reason=reason,
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        """Return validation rules specific to this agent."""
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        """Return reducers used by this agent to update goal state."""
        return []

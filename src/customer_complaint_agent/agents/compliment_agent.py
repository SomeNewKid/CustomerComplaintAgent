"""Deterministic compliment agent placeholder."""

from customer_complaint_agent.domain.entities import Email
from customer_complaint_agent.domain.reducers import EmailEntityReducer
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    AgentDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.validation import ValidationRule


class ComplimentAgent:
    """Agent responsible for compliment email workflows."""

    name = "compliment_agent"

    def decide(self, request: AgentRequest) -> AgentDecision:
        """Return the next deterministic compliment handling decision."""
        email = self._get_email_from_tool_results(request)

        if email is None:
            return ActionDecision(
                tool_name="get_email",
                arguments={"email_id": request.goal_state.root_entity.entity_id},
                reason="Need to inspect the customer email.",
            )

        details: dict[str, object] = {
            "email_template": "reply_to_happy_customer",
        }

        if email.attachment:
            details["email_customization"] = "Thank customer for photo of necklace"

        return FinalDecision(
            completion_type="done",
            details=details,
            reason="Prepared a thank-you response for the happy customer.",
        )

    def get_validation_rules(self) -> list[ValidationRule]:
        """Return validation rules specific to this agent."""
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        """Return reducers used by this agent to update goal state."""
        return [EmailEntityReducer()]

    def _get_email_from_tool_results(self, request: AgentRequest) -> Email | None:
        for tool_result in request.goal_state.tool_results:
            email = tool_result.data.get("email")

            if isinstance(email, Email):
                return email

        return None

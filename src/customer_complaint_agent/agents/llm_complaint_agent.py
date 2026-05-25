"""LLM-backed complaint agent."""

from customer_complaint_agent.domain.reducers import (
    EmailEntityReducer,
    OrderEntityReducer,
    ProductEntityReducer,
)
from customer_complaint_agent.shared.agent import (
    AgentDecision,
    AgentRequest,
    FinalDecision,
)
from customer_complaint_agent.shared.model import ModelClientRegistry, ModelRequest
from customer_complaint_agent.shared.reducer import StateReducer
from customer_complaint_agent.shared.validation import ValidationRule

from .model_decision import (
    agent_decision_from_model_data,
    create_model_decision_schema,
)
from .model_prompt import create_model_user_prompt
from .skill import AgentSkill
from .skills import COMPLAINT_EMAIL_SKILL


class LlmComplaintAgent:
    """Complaint agent that delegates decisions to an AI model."""

    name = "complaint_agent"

    def __init__(
        self,
        model_client_registry: ModelClientRegistry,
        skill: AgentSkill = COMPLAINT_EMAIL_SKILL,
    ) -> None:
        """Create the agent with model clients and its skill."""
        self._model_client_registry = model_client_registry
        self._skill = skill

    def decide(self, request: AgentRequest) -> AgentDecision:
        """Return the next model-backed complaint handling decision."""
        model_client = self._model_client_registry.get_text_client()

        if model_client is None:
            return FinalDecision(
                completion_type="blocked",
                details={"reason_code": "model_client_not_available"},
                reason="No text model client was available.",
            )

        model_request = self._create_model_request(request)
        model_response = model_client.complete(model_request)

        return agent_decision_from_model_data(model_response.data)

    def get_validation_rules(self) -> list[ValidationRule]:
        """Return validation rules specific to this agent."""
        return []

    def get_state_reducers(self) -> list[StateReducer]:
        """Return reducers used by this agent to update goal state."""
        return [
            EmailEntityReducer(),
            OrderEntityReducer(),
            ProductEntityReducer(),
        ]

    def _create_model_request(self, request: AgentRequest) -> ModelRequest:
        user_prompt = create_model_user_prompt(
            skill=self._skill,
            goal_state=request.goal_state,
            tool_registry=request.tool_registry,
        )
        response_schema = create_model_decision_schema(
            request.tool_registry, self._skill
        )

        return ModelRequest(
            system_prompt=(
                "You make structured decisions for an agent harness. Return only "
                "data that matches the provided structured output schema."
            ),
            user_prompt=user_prompt,
            input_data={},
            response_schema=response_schema,
            response_schema_name="agent_decision",
        )

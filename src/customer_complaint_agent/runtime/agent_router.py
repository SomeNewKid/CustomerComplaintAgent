"""Runtime routing for customer email agents."""

from dataclasses import dataclass

from customer_complaint_agent.domain.entities import Email


@dataclass(frozen=True)
class AgentRoute:
    """Selected agent route for an email."""

    agent_name: str
    reason: str


class AgentRouter:
    """Route customer emails to the appropriate agent."""

    def route(self, email: Email) -> AgentRoute:
        """Return the agent route for an email."""
        # Placeholder routing: later this can classify the email contents instead.
        if email.email_id in {"E003", "E004"}:
            return AgentRoute(
                agent_name="compliment_agent",
                reason="Email ID is mapped to the compliment agent.",
            )

        return AgentRoute(
            agent_name="complaint_agent",
            reason="Email ID is mapped to the complaint agent.",
        )

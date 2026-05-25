"""Runtime registry for resolving agents by name."""

from collections.abc import Mapping

from customer_complaint_agent.agents.deterministic_complaint_agent import (
    DeterministicComplaintAgent,
)
from customer_complaint_agent.agents.deterministic_compliment_agent import (
    DeterministicComplimentAgent,
)
from customer_complaint_agent.shared.agent import Agent


class AgentRegistry:
    """Registry of available agents."""

    def __init__(self, agents: Mapping[str, Agent] | None = None) -> None:
        """Create a registry with default agents unless agents are provided."""
        if agents is None:
            agents = {
                DeterministicComplaintAgent.name: DeterministicComplaintAgent(),
                DeterministicComplimentAgent.name: DeterministicComplimentAgent(),
            }

        self._agents = dict(agents)

    def get(self, agent_name: str) -> Agent | None:
        """Return an agent by name, if one is registered."""
        return self._agents.get(agent_name)

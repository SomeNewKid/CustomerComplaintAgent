"""Goal state shared by agents and the harness."""

from dataclasses import dataclass
from enum import StrEnum


class GoalStatus(StrEnum):
    """Lifecycle status for an agent goal."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class EntityRef:
    """Reference to a domain entity involved in a task."""

    entity_type: str
    entity_id: str


@dataclass(frozen=True)
class ToolResult:
    """Structured result returned by a tool call."""

    tool_name: str
    arguments: dict[str, object]
    data: dict[str, object]


@dataclass(frozen=True)
class Claim:
    """Validated structured claim recorded during an agent run."""

    claim_type: str
    source: EntityRef
    supporting_text: str


@dataclass(frozen=True)
class Fact:
    """Validated structured fact recorded during an agent run."""

    fact_type: str
    source: EntityRef
    data: dict[str, object]


@dataclass(frozen=True)
class GoalOutput:
    """Concrete output produced while working on a goal."""

    output_type: str
    data: dict[str, object]


@dataclass(frozen=True)
class GoalResult:
    """Structured result recorded for a goal."""

    result_type: str
    data: dict[str, object]


@dataclass
class GoalState:
    """Harness-owned state for one agent goal."""

    goal_id: str
    status: GoalStatus
    root_entity: EntityRef
    entities: list[EntityRef]
    tool_results: list[ToolResult]
    claims: list[Claim]
    facts: list[Fact]
    outputs: list[GoalOutput]
    results: list[GoalResult]

    def set_entity_reference(self, entity_reference: EntityRef) -> None:
        """Set an entity reference, raising an error for conflicting values."""
        for entity in self.entities:
            if entity.entity_type != entity_reference.entity_type:
                continue

            if entity.entity_id == entity_reference.entity_id:
                return

            raise RuntimeError(
                f"Conflicting entity reference for {entity_reference.entity_type}."
            )

        self.entities.append(entity_reference)

    def add_claim(
        self,
        claim_type: str,
        source: EntityRef,
        supporting_text: str,
    ) -> None:
        """Add a claim to the goal state."""
        self.claims.append(
            Claim(
                claim_type=claim_type,
                source=source,
                supporting_text=supporting_text,
            )
        )

    def add_fact(
        self,
        fact_type: str,
        source: EntityRef,
        data: dict[str, object],
    ) -> None:
        """Add a fact to the goal state."""
        self.facts.append(
            Fact(
                fact_type=fact_type,
                source=source,
                data=data,
            )
        )

    def add_output(
        self,
        output_type: str,
        data: dict[str, object],
    ) -> None:
        """Add an output to the goal state."""
        self.outputs.append(
            GoalOutput(
                output_type=output_type,
                data=data,
            )
        )

"""Runtime goal state creation."""

from customer_complaint_agent.shared.state import EntityRef, GoalState, GoalStatus


def create_email_goal_state(email_id: str) -> GoalState:
    """Create goal state for handling one email."""
    root_entity = EntityRef(entity_type="email", entity_id=email_id)
    return GoalState(
        goal_id=f"handle-email-{email_id}",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=[],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )

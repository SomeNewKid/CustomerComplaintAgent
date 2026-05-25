from customer_complaint_agent.shared.state import (
    Claim,
    EntityRef,
    Fact,
    GoalOutput,
    GoalState,
    GoalStatus,
)


def test_goal_state_adds_claim() -> None:
    goal_state = _goal_state()

    goal_state.add_claim(
        claim_type="damaged_product",
        data={"supporting_text": "the handle is broken"},
    )

    assert goal_state.claims == [
        Claim(
            claim_type="damaged_product",
            data={"supporting_text": "the handle is broken"},
        )
    ]


def test_goal_state_adds_fact() -> None:
    goal_state = _goal_state()

    goal_state.add_fact(
        fact_type="garment_wear_status",
        data={
            "worn": True,
            "confidence": 0.94,
            "supporting_text": "I wore it once to dinner",
        },
    )

    assert goal_state.facts == [
        Fact(
            fact_type="garment_wear_status",
            data={
                "worn": True,
                "confidence": 0.94,
                "supporting_text": "I wore it once to dinner",
            },
        )
    ]


def test_goal_state_adds_output() -> None:
    goal_state = _goal_state()

    goal_state.add_output(
        output_type="draft_email",
        data={"body": "Thank you for contacting us."},
    )

    assert goal_state.outputs == [
        GoalOutput(
            output_type="draft_email",
            data={"body": "Thank you for contacting us."},
        )
    ]


def _goal_state() -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=[],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )

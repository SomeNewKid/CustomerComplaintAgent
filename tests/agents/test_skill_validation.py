from customer_complaint_agent.agents.skill_validation import SkillStateUpdateRule
from customer_complaint_agent.agents.skills import COMPLAINT_EMAIL_SKILL
from customer_complaint_agent.shared.agent import FinalDecision, StateUpdate
from customer_complaint_agent.shared.state import EntityRef, GoalState, GoalStatus


def test_skill_state_update_rule_accepts_allowed_claim_type() -> None:
    rule = SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)

    errors = rule.validate(
        _decision_with_state_update(
            StateUpdate(
                operation="add_claim",
                arguments={
                    "claim_type": "damaged_product",
                    "data": {"supporting_text": "the handle is broken"},
                },
            )
        ),
        _goal_state(),
    )

    assert errors == []


def test_skill_state_update_rule_rejects_disallowed_claim_type() -> None:
    rule = SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)

    errors = rule.validate(
        _decision_with_state_update(
            StateUpdate(
                operation="add_claim",
                arguments={
                    "claim_type": "wrong_size",
                    "data": {"supporting_text": "the mug is too large"},
                },
            )
        ),
        _goal_state(),
    )

    assert len(errors) == 1
    assert errors[0].code == "invalid_claim_type"


def test_skill_state_update_rule_accepts_allowed_fact_type() -> None:
    rule = SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)

    errors = rule.validate(
        _decision_with_state_update(
            StateUpdate(
                operation="add_fact",
                arguments={
                    "fact_type": "damage_verification",
                    "data": {"damage_verified": True},
                },
            )
        ),
        _goal_state(),
    )

    assert errors == []


def test_skill_state_update_rule_rejects_disallowed_fact_type() -> None:
    rule = SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)

    errors = rule.validate(
        _decision_with_state_update(
            StateUpdate(
                operation="add_fact",
                arguments={
                    "fact_type": "shipping_delay",
                    "data": {"days_late": 10},
                },
            )
        ),
        _goal_state(),
    )

    assert len(errors) == 1
    assert errors[0].code == "invalid_fact_type"


def test_skill_state_update_rule_ignores_unknown_operations() -> None:
    rule = SkillStateUpdateRule(COMPLAINT_EMAIL_SKILL)

    errors = rule.validate(
        _decision_with_state_update(
            StateUpdate(
                operation="unknown_operation",
                arguments={"claim_type": "wrong_size"},
            )
        ),
        _goal_state(),
    )

    assert errors == []


def _decision_with_state_update(state_update: StateUpdate) -> FinalDecision:
    return FinalDecision(
        completion_type="done",
        details={
            "refund_decision": "refund",
            "reason_code": "damaged_cheap_item",
        },
        reason="The complaint has been resolved.",
        state_updates=[state_update],
    )


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

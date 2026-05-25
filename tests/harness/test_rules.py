from customer_complaint_agent.harness.rules import (
    CompletionTypeRule,
    RegisteredToolRule,
    StateUpdateShapeRule,
    ToolNameRule,
)
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    FinalDecision,
    StateUpdate,
)
from customer_complaint_agent.shared.state import (
    EntityRef,
    GoalState,
    GoalStatus,
    ToolResult,
)
from customer_complaint_agent.shared.tool import (
    ToolArgument,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by harness rule tests."
    arguments = (
        ToolArgument(
            name="value",
            argument_type="string",
            description="A fake tool value.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={"attachments_directory": tool_runtime.settings.attachments_directory},
        )


def test_completion_type_rule_ignores_non_final_decision() -> None:
    rule = CompletionTypeRule()
    decision = ActionDecision(
        tool_name="get_email",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_completion_type_rule_accepts_done_completion_type() -> None:
    rule = CompletionTypeRule()
    decision = FinalDecision(
        completion_type="done",
        details={},
        reason="The goal is complete.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_completion_type_rule_rejects_invalid_completion_type() -> None:
    rule = CompletionTypeRule()
    decision = FinalDecision(
        completion_type="invalid_value",
        details={},
        reason="The goal is complete.",
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "invalid_completion_type"


def test_completion_type_rule_rejects_missing_completion_type() -> None:
    rule = CompletionTypeRule()
    decision = FinalDecision(
        completion_type="",
        details={},
        reason="The goal is complete.",
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_completion_type"


def test_tool_name_rule_ignores_non_action_decision() -> None:
    rule = ToolNameRule()
    decision = FinalDecision(
        completion_type="done",
        details={},
        reason="The goal is complete.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_tool_name_rule_accepts_present_tool_name() -> None:
    rule = ToolNameRule()
    decision = ActionDecision(
        tool_name="get_email",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_tool_name_rule_rejects_missing_tool_name() -> None:
    rule = ToolNameRule()
    decision = ActionDecision(
        tool_name="",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_tool_name"


def test_registered_tool_rule_ignores_non_action_decision() -> None:
    rule = RegisteredToolRule(ToolRegistry(tools=(_FakeTool(),)))
    decision = FinalDecision(
        completion_type="done",
        details={},
        reason="The goal is complete.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_registered_tool_rule_ignores_missing_tool_name() -> None:
    rule = RegisteredToolRule(ToolRegistry(tools=(_FakeTool(),)))
    decision = ActionDecision(
        tool_name="",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_registered_tool_rule_accepts_registered_tool_name() -> None:
    rule = RegisteredToolRule(ToolRegistry(tools=(_FakeTool(),)))
    decision = ActionDecision(
        tool_name="fake_tool",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_registered_tool_rule_rejects_unknown_tool_name() -> None:
    rule = RegisteredToolRule(ToolRegistry(tools=(_FakeTool(),)))
    decision = ActionDecision(
        tool_name="missing_tool",
        arguments={"email_id": "E001"},
        reason="Need to inspect the email.",
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "unknown_tool"
    assert errors[0].message == "Tool 'missing_tool' is not registered."


def test_state_update_shape_rule_rejects_unknown_operation() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="replace_claims",
            arguments={},
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "unknown_state_update_operation"


def test_state_update_shape_rule_rejects_missing_claim_type() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_claim",
            arguments={
                "data": {"supporting_text": "the handle is broken"},
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_claim_type"


def test_state_update_shape_rule_rejects_claim_with_missing_data() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_claim",
            arguments={
                "claim_type": "damaged_product",
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_data"


def test_state_update_shape_rule_accepts_valid_add_claim() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_claim",
            arguments={
                "claim_type": "damaged_product",
                "data": {"supporting_text": "the handle is broken"},
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def test_state_update_shape_rule_rejects_missing_fact_type() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_fact",
            arguments={
                "data": {"damage_verified": True},
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_fact_type"


def test_state_update_shape_rule_rejects_fact_with_missing_data() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_fact",
            arguments={
                "fact_type": "damage_verification",
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert len(errors) == 1
    assert errors[0].code == "missing_data"


def test_state_update_shape_rule_accepts_valid_add_fact() -> None:
    rule = StateUpdateShapeRule()
    decision = _decision_with_state_update(
        StateUpdate(
            operation="add_fact",
            arguments={
                "fact_type": "damage_verification",
                "data": {"damage_verified": True},
            },
        )
    )

    errors = rule.validate(decision, _goal_state())

    assert errors == []


def _decision_with_state_update(state_update: StateUpdate) -> FinalDecision:
    return FinalDecision(
        completion_type="done",
        details={},
        reason="The goal is complete.",
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

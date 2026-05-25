from typing import cast

import pytest

from customer_complaint_agent.agents.model_decision import (
    agent_decision_from_model_data,
    create_model_decision_schema,
)
from customer_complaint_agent.agents.skills import COMPLAINT_EMAIL_SKILL
from customer_complaint_agent.shared.agent import (
    ActionDecision,
    FinalDecision,
    StateUpdate,
)
from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import (
    ToolArgument,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from customer_complaint_agent.shared.vocabulary import (
    COMPLETION_TYPES,
    STATE_UPDATE_OPERATIONS,
)


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by model decision tests."
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
            data={},
        )


def test_create_model_decision_schema_includes_top_level_fields() -> None:
    schema = create_model_decision_schema(
        ToolRegistry(tools=(_FakeTool(),)),
        COMPLAINT_EMAIL_SKILL,
    )

    assert schema["required"] == [
        "reason",
        "state_updates",
        "action_decision",
        "final_decision",
    ]


def test_create_model_decision_schema_includes_tool_action_branch() -> None:
    tool = _FakeTool()
    schema = create_model_decision_schema(
        ToolRegistry(tools=(tool,)),
        COMPLAINT_EMAIL_SKILL,
    )
    properties = _schema_properties(schema)
    action_decision = properties["action_decision"]
    assert isinstance(action_decision, dict)
    action_decision_schema = cast(dict[str, object], action_decision)
    action_options = _schema_list(action_decision_schema["anyOf"])

    assert action_options[1] == {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tool_name": {
                "type": "string",
                "enum": [tool.name],
            },
            "arguments": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "A fake tool value.",
                    },
                },
                "required": ["value"],
            },
        },
        "required": ["tool_name", "arguments"],
    }


def test_create_model_decision_schema_includes_completion_types() -> None:
    schema = create_model_decision_schema(
        ToolRegistry(tools=(_FakeTool(),)),
        COMPLAINT_EMAIL_SKILL,
    )
    properties = _schema_properties(schema)
    final_decision = _object_option(properties["final_decision"])
    final_properties = _schema_properties(final_decision)
    completion_type = final_properties["completion_type"]
    assert isinstance(completion_type, dict)

    assert completion_type["enum"] == list(COMPLETION_TYPES)


def test_create_model_decision_schema_includes_state_update_operations() -> None:
    schema = create_model_decision_schema(
        ToolRegistry(tools=(_FakeTool(),)),
        COMPLAINT_EMAIL_SKILL,
    )
    properties = _schema_properties(schema)
    state_updates = properties["state_updates"]
    assert isinstance(state_updates, dict)
    state_updates_schema = cast(dict[str, object], state_updates)
    state_update_items = cast(dict[str, object], state_updates_schema["items"])
    state_update_options = _schema_list(state_update_items["anyOf"])
    operation_values: list[object] = []

    for state_update_option in state_update_options:
        state_update_properties = _schema_properties(state_update_option)
        operation = state_update_properties["operation"]
        operation_schema = _schema_dict(operation)
        operation_enum = _schema_list(operation_schema["enum"])
        operation_values.append(operation_enum[0])

    assert operation_values == sorted(STATE_UPDATE_OPERATIONS)


def test_create_model_decision_schema_includes_final_detail_fields() -> None:
    schema = create_model_decision_schema(
        ToolRegistry(tools=(_FakeTool(),)),
        COMPLAINT_EMAIL_SKILL,
    )
    properties = _schema_properties(schema)
    final_decision = _object_option(properties["final_decision"])
    final_properties = _schema_properties(final_decision)
    details = final_properties["details"]
    details_properties = _schema_properties(details)

    assert list(details_properties) == ["refund_decision", "reason_code"]


def test_model_decision_converts_action_decision() -> None:
    decision = agent_decision_from_model_data(
        {
            "reason": "Need to load the email.",
            "state_updates": [],
            "action_decision": {
                "tool_name": "get_email",
                "arguments": {"email_id": "E001"},
            },
            "final_decision": None,
        }
    )

    assert decision == ActionDecision(
        reason="Need to load the email.",
        state_updates=[],
        tool_name="get_email",
        arguments={"email_id": "E001"},
    )


def test_model_decision_converts_final_decision() -> None:
    decision = agent_decision_from_model_data(
        {
            "reason": "Refund policy evaluation is complete.",
            "state_updates": [],
            "action_decision": None,
            "final_decision": {
                "completion_type": "done",
                "details": {
                    "refund_decision": "refund",
                    "reason_code": "damaged_cheap_item",
                },
            },
        }
    )

    assert decision == FinalDecision(
        reason="Refund policy evaluation is complete.",
        state_updates=[],
        completion_type="done",
        details={
            "refund_decision": "refund",
            "reason_code": "damaged_cheap_item",
        },
    )


def test_model_decision_converts_action_decision_state_updates() -> None:
    decision = agent_decision_from_model_data(
        {
            "reason": "Need to load the email.",
            "state_updates": [
                {
                    "operation": "add_claim",
                    "arguments": {
                        "claim_type": "damaged_product",
                        "data": {"supporting_text": "the handle is broken"},
                    },
                }
            ],
            "action_decision": {
                "tool_name": "get_email",
                "arguments": {"email_id": "E001"},
            },
            "final_decision": None,
        }
    )

    assert decision == ActionDecision(
        reason="Need to load the email.",
        state_updates=[
            StateUpdate(
                operation="add_claim",
                arguments={
                    "claim_type": "damaged_product",
                    "data": {"supporting_text": "the handle is broken"},
                },
            )
        ],
        tool_name="get_email",
        arguments={"email_id": "E001"},
    )


def test_model_decision_converts_final_decision_state_updates() -> None:
    decision = agent_decision_from_model_data(
        {
            "reason": "Refund policy evaluation is complete.",
            "state_updates": [
                {
                    "operation": "add_fact",
                    "arguments": {
                        "fact_type": "refund_policy_evaluated",
                        "data": {"refund_decision": "refund"},
                    },
                }
            ],
            "action_decision": None,
            "final_decision": {
                "completion_type": "done",
                "details": {
                    "refund_decision": "refund",
                    "reason_code": "damaged_cheap_item",
                },
            },
        }
    )

    assert decision == FinalDecision(
        reason="Refund policy evaluation is complete.",
        state_updates=[
            StateUpdate(
                operation="add_fact",
                arguments={
                    "fact_type": "refund_policy_evaluated",
                    "data": {"refund_decision": "refund"},
                },
            )
        ],
        completion_type="done",
        details={
            "refund_decision": "refund",
            "reason_code": "damaged_cheap_item",
        },
    )


def test_model_decision_rejects_both_decision_branches() -> None:
    with pytest.raises(
        ValueError,
        match="Model decision cannot include both decision branches.",
    ):
        agent_decision_from_model_data(
            {
                "reason": "Conflicting decision.",
                "state_updates": [],
                "action_decision": {
                    "tool_name": "get_email",
                    "arguments": {"email_id": "E001"},
                },
                "final_decision": {
                    "completion_type": "done",
                    "details": {},
                },
            }
        )


def test_model_decision_rejects_missing_decision_branch() -> None:
    with pytest.raises(
        ValueError,
        match="Model decision must include one decision branch.",
    ):
        agent_decision_from_model_data(
            {
                "reason": "No decision was selected.",
                "state_updates": [],
                "action_decision": None,
                "final_decision": None,
            }
        )


def test_model_decision_rejects_missing_reason() -> None:
    with pytest.raises(ValueError, match="Model decision reason is required."):
        agent_decision_from_model_data(
            {
                "state_updates": [],
                "action_decision": {
                    "tool_name": "get_email",
                    "arguments": {"email_id": "E001"},
                },
                "final_decision": None,
            }
        )


def test_model_decision_rejects_malformed_state_updates() -> None:
    with pytest.raises(
        ValueError,
        match="Model decision state_updates must be a list.",
    ):
        agent_decision_from_model_data(
            {
                "reason": "Need to load the email.",
                "state_updates": "not a list",
                "action_decision": {
                    "tool_name": "get_email",
                    "arguments": {"email_id": "E001"},
                },
                "final_decision": None,
            }
        )


def _schema_properties(schema: object) -> dict[str, object]:
    schema_dictionary = _schema_dict(schema)
    properties = schema_dictionary["properties"]
    assert isinstance(properties, dict)
    return cast(dict[str, object], properties)


def _schema_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _schema_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def _object_option(schema: object) -> dict[str, object]:
    schema_dictionary = _schema_dict(schema)
    options = _schema_list(schema_dictionary["anyOf"])
    object_options: list[dict[str, object]] = []

    for option in options:
        if not isinstance(option, dict):
            continue

        option_dictionary = cast(dict[str, object], option)

        if option_dictionary.get("type") == "object":
            object_options.append(option_dictionary)

    assert len(object_options) == 1
    return object_options[0]

"""Prompt creation for model-backed agents."""

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, cast

from customer_complaint_agent.agents.skill import AgentSkill, FinalDetailField
from customer_complaint_agent.shared.state import GoalState
from customer_complaint_agent.shared.tool import ToolRegistry
from customer_complaint_agent.shared.vocabulary import (
    COMPLETION_TYPES,
    STATE_UPDATE_OPERATIONS,
)


def create_model_user_prompt(
    skill: AgentSkill,
    goal_state: GoalState,
    tool_registry: ToolRegistry,
) -> str:
    """Create prompt text for a model decision request."""
    sections = [
        "You are deciding the next step for an agent goal.",
        _agent_goal_section(skill),
        _agent_instructions_section(skill),
        _decision_rules_section(),
        _what_not_to_do_section(),
        _output_requirement_section(),
        _available_tools_section(tool_registry),
        _completion_types_section(),
        _state_update_operations_section(),
        _claim_types_section(skill),
        _fact_types_section(skill),
        _final_detail_fields_section(skill),
        _goal_state_section(goal_state),
        _tool_results_section(goal_state),
    ]

    return "\n\n".join(section for section in sections if section)


def _agent_goal_section(skill: AgentSkill) -> str:
    return f"Agent goal:\n{skill.goal}"


def _agent_instructions_section(skill: AgentSkill) -> str:
    if not skill.instructions:
        return ""

    return f"Agent instructions:\n{skill.instructions}"


def _decision_rules_section() -> str:
    return "\n".join(
        [
            "Decision rules:",
            (
                "- You are participating in an agent loop. On each turn, you must "
                "choose the single next step that best advances the current goal."
            ),
            (
                "- Return an action_decision when the agent needs information or "
                "verification from an available tool before it can safely finish."
            ),
            (
                "- Return a final_decision when the agent has enough information "
                "to complete the goal, or when the goal cannot continue because "
                "required information or conditions are missing and cannot be "
                "obtained using available tools."
            ),
            (
                "- Set exactly one of action_decision or final_decision to an "
                "object. Set the other field to null."
            ),
            (
                "- Do not request a tool unless it is listed in the available "
                "tools section."
            ),
            (
                "- Do not invent tool results, entity data, facts, claims, or "
                "policy tool results. Use only the current goal state and prior "
                "tool results."
            ),
            (
                "- Do not repeat a tool call with the same arguments unless the "
                "prior result is unusable and your reason explains why."
            ),
            (
                "- A claim is something asserted by the customer or another "
                "external source, such as 'the handle is broken' or 'the delivery "
                "was late.' Use add_claim only when the assertion is directly "
                "supported by source text or prior tool results."
            ),
            (
                "- A fact is something the agent has verified from available data "
                "or tool results, such as 'the order was already refunded' or "
                "'the attachment shows visible product damage.' Use add_fact only "
                "when the value is directly supported by the current goal state or "
                "prior tool results."
            ),
            (
                "- Do not use add_fact for a customer assertion that has not been "
                "verified. Record it as a claim instead."
            ),
            (
                "- Do not use state_updates to record outputs, side effects, tool "
                "calls, or final decisions."
            ),
            "- Keep reason brief and explain why this specific next step was chosen.",
        ]
    )


def _what_not_to_do_section() -> str:
    return "\n".join(
        [
            "What not to do:",
            "- Do not invent tool results.",
            "- Do not assume missing entities.",
            "- Do not call unavailable tools.",
            (
                "- Do not return a final refund decision until required facts "
                "are available."
            ),
            (
                "- Do not request a tool already called with the same arguments "
                "unless there is a reason."
            ),
            "- Do not use claim type values as fact types.",
            "- Do not use fact type values as claim types.",
            "- Do not use final detail values in state_updates.",
            "- Do not use state update operation names in final_decision.details.",
        ]
    )


def _output_requirement_section() -> str:
    return "\n".join(
        [
            "Output requirement:",
            "- Your response must match the provided structured output schema.",
            "- Do not include free-form text outside the structured response.",
        ]
    )


def _available_tools_section(tool_registry: ToolRegistry) -> str:
    lines = ["Available tools:"]

    for tool in tool_registry.tools:
        lines.append(f"- {tool.name}: {tool.description}")
        lines.append("  Arguments:")

        for argument in tool.arguments:
            lines.append(
                f"  - {argument.name} ({argument.argument_type}): "
                f"{argument.description}"
            )

    return "\n".join(lines)


def _completion_types_section() -> str:
    lines = ["Completion types:"]

    for completion_type, description in COMPLETION_TYPES.items():
        lines.append(f"- {completion_type}: {description}")

    return "\n".join(lines)


def _state_update_operations_section() -> str:
    lines = ["State update operations:"]

    for operation, operation_metadata in sorted(STATE_UPDATE_OPERATIONS.items()):
        lines.append(f"- {operation}: {operation_metadata.description}")
        lines.append("  Arguments:")

        for argument in operation_metadata.arguments:
            lines.append(
                f"  - {argument.name} ({argument.argument_type}): "
                f"{argument.description}"
            )

    return "\n".join(lines)


def _claim_types_section(skill: AgentSkill) -> str:
    if not skill.claim_types:
        return ""

    lines = [
        "Allowed claim types:",
        "Use these values only in state_updates entries whose operation is add_claim.",
    ]

    for claim_type, description in sorted(skill.claim_types.items()):
        lines.append(f"- {claim_type}: {description}")

    return "\n".join(lines)


def _fact_types_section(skill: AgentSkill) -> str:
    if not skill.fact_types:
        return ""

    lines = [
        "Allowed fact types:",
        "Use these values only in state_updates entries whose operation is add_fact.",
    ]

    for fact_type, description in sorted(skill.fact_types.items()):
        lines.append(f"- {fact_type}: {description}")

    return "\n".join(lines)


def _final_detail_fields_section(skill: AgentSkill) -> str:
    if not skill.final_detail_fields:
        return ""

    lines = [
        "Final detail fields:",
        "Use these fields only in final_decision.details.",
    ]

    for field_name, field_metadata in sorted(skill.final_detail_fields.items()):
        field_lines = _final_detail_field_lines(field_name, field_metadata)
        lines.extend(field_lines)

    return "\n".join(lines)


def _final_detail_field_lines(
    field_name: str,
    field_metadata: FinalDetailField,
) -> list[str]:
    lines = [f"- {field_name}: {field_metadata.description}"]

    if not field_metadata.allowed_values:
        lines.append("  Allowed values: any value that satisfies the description.")
        return lines

    lines.append("  Allowed values:")

    for value, description in sorted(field_metadata.allowed_values.items()):
        lines.append(f"  - {value}: {description}")

    return lines


def _goal_state_section(goal_state: GoalState) -> str:
    json_safe_goal_state = _json_safe_goal_state(goal_state)
    serialized_goal_state = json.dumps(
        json_safe_goal_state,
        indent=2,
        sort_keys=True,
    )
    return f"Current goal state:\n{serialized_goal_state}"


def _tool_results_section(goal_state: GoalState) -> str:
    json_safe_tool_results = _json_safe_value(goal_state.tool_results)
    serialized_tool_results = json.dumps(
        json_safe_tool_results,
        indent=2,
        sort_keys=True,
    )
    return f"Prior tool results:\n{serialized_tool_results}"


def _json_safe_goal_state(goal_state: GoalState) -> dict[str, object]:
    goal_state_data = _json_safe_value(goal_state)
    goal_state_dict = cast(dict[str, object], goal_state_data)
    return {
        key: value for key, value in goal_state_dict.items() if key != "tool_results"
    }


def _json_safe_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        dataclass_value = cast(Any, value)
        dataclass_dict = asdict(dataclass_value)
        return _json_safe_value(dataclass_dict)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        dict_value = cast(dict[object, object], value)
        return {str(key): _json_safe_value(item) for key, item in dict_value.items()}

    if isinstance(value, list):
        list_value = cast(list[object], value)
        return [_json_safe_value(item) for item in list_value]

    if isinstance(value, tuple):
        tuple_value = cast(tuple[object, ...], value)
        return [_json_safe_value(item) for item in tuple_value]

    return value

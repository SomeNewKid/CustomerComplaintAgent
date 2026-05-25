from customer_complaint_agent.agents.model_prompt import create_model_user_prompt
from customer_complaint_agent.agents.skills import COMPLAINT_EMAIL_SKILL
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
from customer_complaint_agent.shared.vocabulary import (
    COMPLETION_TYPES,
    STATE_UPDATE_OPERATIONS,
)


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by model prompt tests."
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


def test_create_model_user_prompt_includes_allowed_tool_names() -> None:
    prompt = _create_model_user_prompt()

    assert "fake_tool" in prompt


def test_create_model_user_prompt_includes_tool_argument_details() -> None:
    prompt = _create_model_user_prompt()

    assert "value" in prompt
    assert "string" in prompt
    assert "A fake tool value." in prompt


def test_create_model_user_prompt_includes_completion_types() -> None:
    prompt = _create_model_user_prompt()

    for completion_type in COMPLETION_TYPES:
        assert completion_type in prompt


def test_create_model_user_prompt_includes_state_update_operations() -> None:
    prompt = _create_model_user_prompt()

    for operation, operation_metadata in STATE_UPDATE_OPERATIONS.items():
        assert operation in prompt
        assert operation_metadata.description in prompt


def test_create_model_user_prompt_includes_state_update_argument_details() -> None:
    prompt = _create_model_user_prompt()

    for operation_metadata in STATE_UPDATE_OPERATIONS.values():
        for argument in operation_metadata.arguments:
            assert argument.name in prompt
            assert argument.argument_type in prompt
            assert argument.description in prompt


def test_create_model_user_prompt_includes_goal_state_data() -> None:
    prompt = _create_model_user_prompt()

    assert "handle-email-E001" in prompt
    assert "email" in prompt
    assert "E001" in prompt


def test_create_model_user_prompt_has_separate_tool_results_section() -> None:
    prompt = create_model_user_prompt(
        skill=COMPLAINT_EMAIL_SKILL,
        goal_state=_goal_state(
            tool_results=[
                ToolResult(
                    tool_name="get_email",
                    arguments={"email_id": "E001"},
                    data={"message": "The handle is broken."},
                )
            ],
        ),
        tool_registry=ToolRegistry(tools=(_FakeTool(),)),
    )
    goal_state_section = prompt.split("Prior tool results:")[0]
    tool_results_section = prompt.split("Prior tool results:")[1]

    assert "tool_results" not in goal_state_section
    assert "get_email" in tool_results_section
    assert "The handle is broken." in tool_results_section


def test_create_model_user_prompt_includes_what_not_to_do_section() -> None:
    prompt = _create_model_user_prompt()

    assert "What not to do:" in prompt
    assert "Do not invent tool results." in prompt
    assert "Do not assume missing entities." in prompt
    assert "Do not call unavailable tools." in prompt
    assert "Do not return a final refund decision" in prompt
    assert "Do not request a tool already called with the same arguments" in prompt


def test_create_model_user_prompt_includes_output_requirement() -> None:
    prompt = _create_model_user_prompt()

    assert "Output requirement:" in prompt
    assert "must match the provided structured output schema" in prompt
    assert "Do not include free-form text" in prompt


def test_create_model_user_prompt_includes_skill_goal() -> None:
    prompt = _create_model_user_prompt()

    assert "Agent goal:" in prompt
    assert COMPLAINT_EMAIL_SKILL.goal in prompt


def test_create_model_user_prompt_includes_skill_instructions() -> None:
    prompt = _create_model_user_prompt()

    assert "Agent instructions:" in prompt
    assert COMPLAINT_EMAIL_SKILL.instructions in prompt


def test_create_model_user_prompt_does_not_include_skill_name() -> None:
    prompt = _create_model_user_prompt()

    assert "Agent skill:" not in prompt
    assert COMPLAINT_EMAIL_SKILL.name not in prompt


def test_create_model_user_prompt_includes_skill_claim_types() -> None:
    prompt = _create_model_user_prompt()

    assert "Use these values only in state_updates entries" in prompt
    assert "operation is add_claim" in prompt

    for claim_type, description in COMPLAINT_EMAIL_SKILL.claim_types.items():
        assert claim_type in prompt
        assert description in prompt


def test_create_model_user_prompt_includes_skill_fact_types() -> None:
    prompt = _create_model_user_prompt()

    assert "operation is add_fact" in prompt

    for fact_type, description in COMPLAINT_EMAIL_SKILL.fact_types.items():
        assert fact_type in prompt
        assert description in prompt


def test_create_model_user_prompt_includes_skill_final_detail_fields() -> None:
    prompt = _create_model_user_prompt()

    assert "Use these fields only in final_decision.details." in prompt

    for field_name, field_metadata in COMPLAINT_EMAIL_SKILL.final_detail_fields.items():
        assert field_name in prompt
        assert field_metadata.description in prompt

        if field_metadata.allowed_values is None:
            continue

        for value, description in field_metadata.allowed_values.items():
            assert value in prompt
            assert description in prompt


def test_create_model_user_prompt_warns_against_vocabulary_cross_use() -> None:
    prompt = _create_model_user_prompt()

    assert "Do not use claim type values as fact types." in prompt
    assert "Do not use fact type values as claim types." in prompt
    assert "Do not use final detail values in state_updates." in prompt
    assert (
        "Do not use state update operation names in final_decision.details." in prompt
    )


def _create_model_user_prompt() -> str:
    return create_model_user_prompt(
        skill=COMPLAINT_EMAIL_SKILL,
        goal_state=_goal_state(),
        tool_registry=ToolRegistry(tools=(_FakeTool(),)),
    )


def _goal_state(tool_results: list[ToolResult] | None = None) -> GoalState:
    root_entity = EntityRef(entity_type="email", entity_id="E001")
    return GoalState(
        goal_id="handle-email-E001",
        status=GoalStatus.RUNNING,
        root_entity=root_entity,
        entities=[root_entity],
        tool_results=tool_results or [],
        claims=[],
        facts=[],
        outputs=[],
        results=[],
    )

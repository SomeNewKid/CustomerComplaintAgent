from pathlib import Path

import pytest

from customer_complaint_agent.harness.tool_executor import ToolExecutor
from customer_complaint_agent.shared.model import ModelClientRegistry
from customer_complaint_agent.shared.settings import Settings
from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import (
    ToolArgument,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)


class _FakeTool:
    name = "fake_tool"
    description = "Fake tool used by tool executor tests."
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


def test_tool_executor_executes_registered_tool() -> None:
    executor = ToolExecutor(tool_registry=ToolRegistry(tools=(_FakeTool(),)))

    result = executor.execute(
        "fake_tool",
        {"value": "example"},
        _tool_runtime(),
    )

    assert result.tool_name == "fake_tool"
    assert result.arguments == {"value": "example"}
    assert result.data == {
        "attachments_directory": Path("data/attachments"),
    }


def test_tool_executor_raises_error_for_unregistered_tool() -> None:
    executor = ToolExecutor(tool_registry=ToolRegistry(tools=(_FakeTool(),)))

    with pytest.raises(ValueError, match="Tool 'missing_tool' is not registered."):
        executor.execute(
            "missing_tool",
            {"value": "example"},
            _tool_runtime(),
        )


def _tool_runtime() -> ToolRuntime:
    return ToolRuntime(
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=3,
            max_paid_model_calls=0,
        ),
        model_client_registry=ModelClientRegistry(clients=()),
    )

import pytest

from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import (
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)


class _FakeTool:
    name = "fake_tool"

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


class _DuplicateFakeTool:
    name = "fake_tool"

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


def test_tool_registry_get_returns_named_tool() -> None:
    tool = _FakeTool()
    registry = ToolRegistry(tools=(tool,))

    assert registry.get("fake_tool") is tool


def test_tool_registry_get_returns_none_for_unknown_tool() -> None:
    registry = ToolRegistry(tools=(_FakeTool(),))

    assert registry.get("missing_tool") is None


def test_tool_registry_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValueError, match="Duplicate tool name: fake_tool"):
        ToolRegistry(tools=(_FakeTool(), _DuplicateFakeTool()))

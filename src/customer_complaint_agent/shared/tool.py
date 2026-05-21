"""Tool contracts shared by the harness and domain tools."""

from dataclasses import dataclass
from typing import Protocol

from .settings import Settings
from .state import ToolResult

ToolRequest = dict[str, object]


@dataclass(frozen=True)
class ToolRuntime:
    """Harness-provided runtime values hidden from the LLM tool request."""

    settings: Settings


class Tool(Protocol):
    """Protocol implemented by tools executed by the harness."""

    name: str

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        ...


@dataclass(frozen=True)
class ToolRegistry:
    """Collection of tools available to an agent run."""

    tools: tuple[Tool, ...]

    def __post_init__(self) -> None:
        tool_names: list[str] = []

        for tool in self.tools:
            if tool.name in tool_names:
                raise ValueError(f"Duplicate tool name: {tool.name}")

            tool_names.append(tool.name)

    def get(self, tool_name: str) -> Tool | None:
        """Return the named tool, if available."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool

        return None

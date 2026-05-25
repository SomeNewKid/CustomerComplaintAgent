"""Damage verification tools."""

from pathlib import Path

from customer_complaint_agent.shared.model import ModelRequest, ModelResponse
from customer_complaint_agent.shared.state import ToolResult
from customer_complaint_agent.shared.tool import ToolArgument, ToolRequest, ToolRuntime


class VerifyDamagedProductTool:
    """Tool that verifies whether an attachment shows product damage."""

    name = "verify_damaged_product"
    description = "Verify whether an attachment image shows product damage."
    arguments = (
        ToolArgument(
            name="filename",
            argument_type="string",
            description="The filename of the product photo attachment.",
        ),
    )

    def execute(
        self,
        tool_request: ToolRequest,
        tool_runtime: ToolRuntime,
    ) -> ToolResult:
        """Execute the tool with structured arguments."""
        filename = str(tool_request["filename"])
        attachment_path = tool_runtime.settings.attachments_directory / filename
        attachment_exists = attachment_path.is_file()

        if not attachment_exists:
            return ToolResult(
                tool_name=self.name,
                arguments=tool_request,
                data={
                    "filename": filename,
                    "attachment_exists": False,
                    "damage_verified": False,
                    "confidence": 0.0,
                    "supporting_text": "Attachment file was not found.",
                },
            )

        vision_client = tool_runtime.model_client_registry.get_vision_client()

        if vision_client is None:
            return ToolResult(
                tool_name=self.name,
                arguments=tool_request,
                data={
                    "filename": filename,
                    "attachment_exists": True,
                    "damage_verified": None,
                    "confidence": 0.0,
                    "supporting_text": "No vision model client was available.",
                },
            )

        model_request = self._create_model_request(attachment_path)
        model_response = vision_client.complete(model_request)

        return ToolResult(
            tool_name=self.name,
            arguments=tool_request,
            data={
                "filename": filename,
                "attachment_exists": True,
                "damage_verified": self._damage_verified(model_response),
                "confidence": self._confidence(model_response),
                "supporting_text": self._supporting_text(model_response),
            },
        )

    def _create_model_request(self, attachment_path: Path) -> ModelRequest:
        return ModelRequest(
            system_prompt=(
                "You inspect customer email attachment photos for product damage. "
                "Return only structured JSON that matches the requested schema."
            ),
            user_prompt=(
                "Determine whether the attached image shows a damaged product. "
                "Set damage_verified to true only when visible product damage is "
                "clear from the image."
            ),
            input_data={},
            response_schema={
                "type": "object",
                "properties": {
                    "damage_verified": {"type": "boolean"},
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "supporting_text": {"type": "string"},
                },
                "required": [
                    "damage_verified",
                    "confidence",
                    "supporting_text",
                ],
                "additionalProperties": False,
            },
            response_schema_name="damage_verification",
            image_paths=(attachment_path,),
        )

    def _damage_verified(self, response: ModelResponse) -> bool:
        return bool(response.data["damage_verified"])

    def _confidence(self, response: ModelResponse) -> float:
        confidence = response.data["confidence"]

        if isinstance(confidence, int | float):
            return float(confidence)

        return 0.0

    def _supporting_text(self, response: ModelResponse) -> str:
        return str(response.data["supporting_text"])

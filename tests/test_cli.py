import json

import pytest

from customer_complaint_agent.cli import main
from customer_complaint_agent.harness.runner import RunResult, RunStatus


def test_cli_handles_email_id_and_prints_run_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def email_handler(email_id: str) -> RunResult:
        assert email_id == "E001"
        return RunResult(
            run_id="handle-email-E001",
            status=RunStatus.COMPLETED,
            completion_type="done",
            details={
                "refund_decision": "refund",
                "reason_code": "damaged_cheap_item",
            },
        )

    exit_code = main(["--email_id", "E001"], email_handler)
    output = capsys.readouterr().out
    output_data = json.loads(output)

    assert exit_code == 0
    assert output_data == {
        "run_id": "handle-email-E001",
        "status": "completed",
        "completion_type": "done",
        "details": {
            "refund_decision": "refund",
            "reason_code": "damaged_cheap_item",
        },
    }

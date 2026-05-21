from customer_complaint_agent.harness.runner import RunStatus
from customer_complaint_agent.runtime.email_handler import run_email_handler


def test_harness_handles_e001_with_complaint_agent() -> None:
    result = run_email_handler("E001")

    assert "refund_decision" in result.details


def test_harness_handles_e002_with_complaint_agent() -> None:
    result = run_email_handler("E002")

    assert "refund_decision" in result.details


def test_harness_handles_e003_with_compliment_agent() -> None:
    result = run_email_handler("E003")

    assert result.details["email_template"] == "reply_to_happy_customer"


def test_harness_handles_e004_with_compliment_agent() -> None:
    result = run_email_handler("E004")

    assert result.details["email_template"] == "reply_to_happy_customer"


def test_harness_loop_completes_for_e001() -> None:
    result = run_email_handler("E001")

    assert result.status == RunStatus.COMPLETED


def test_harness_loop_completes_for_e002() -> None:
    result = run_email_handler("E002")

    assert result.status == RunStatus.COMPLETED


def test_harness_loop_completes_for_e003() -> None:
    result = run_email_handler("E003")

    assert result.status == RunStatus.COMPLETED


def test_harness_loop_completes_for_e004() -> None:
    result = run_email_handler("E004")

    assert result.status == RunStatus.COMPLETED


def test_harness_returns_run_id_for_e001() -> None:
    result = run_email_handler("E001")

    assert result.run_id


def test_harness_returns_run_id_for_e002() -> None:
    result = run_email_handler("E002")

    assert result.run_id


def test_harness_returns_run_id_for_e003() -> None:
    result = run_email_handler("E003")

    assert result.run_id


def test_harness_returns_run_id_for_e004() -> None:
    result = run_email_handler("E004")

    assert result.run_id


def test_email_handler_refunds_e001_damaged_cheap_item() -> None:
    result = run_email_handler("E001")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "refund",
        "reason_code": "damaged_cheap_item",
    }


def test_email_handler_escalates_e002_damaged_expensive_item() -> None:
    result = run_email_handler("E002")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "refund_decision": "escalate",
        "reason_code": "damaged_expensive_item",
    }


def test_email_handler_replies_to_e003_happy_customer() -> None:
    result = run_email_handler("E003")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details["email_template"] == "reply_to_happy_customer"
    assert result.details.get("email_customization") in (None, "")


def test_email_handler_replies_to_e004_happy_customer_photo() -> None:
    result = run_email_handler("E004")

    assert result.status == RunStatus.COMPLETED
    assert result.completion_type == "done"
    assert result.details == {
        "email_template": "reply_to_happy_customer",
        "email_customization": "Thank customer for photo of necklace",
    }

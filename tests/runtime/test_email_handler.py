from customer_complaint_agent.harness.runner import RunStatus
from customer_complaint_agent.runtime.email_handler import run_email_handler


def test_harness_routes_e001_to_complaint_agent() -> None:
    result = run_email_handler("E001")

    assert result.details["agent"] == "complaint_agent"


def test_harness_routes_e002_to_complaint_agent() -> None:
    result = run_email_handler("E002")

    assert result.details["agent"] == "complaint_agent"


def test_harness_routes_e003_to_compliment_agent() -> None:
    result = run_email_handler("E003")

    assert result.details["agent"] == "compliment_agent"


def test_harness_routes_e004_to_compliment_agent() -> None:
    result = run_email_handler("E004")

    assert result.details["agent"] == "compliment_agent"


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

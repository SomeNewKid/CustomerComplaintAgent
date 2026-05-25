from pathlib import Path

from customer_complaint_agent.domain.entities import Customer, Email, Order, Product
from customer_complaint_agent.domain.refunds.refund_policy import RefundDecision
from customer_complaint_agent.domain.store import Store
from customer_complaint_agent.domain.tools import (
    EvaluateRefundPolicyTool,
    GetCustomerTool,
    GetEmailTool,
    GetOrderTool,
    GetProductTool,
    VerifyDamagedProductTool,
)
from customer_complaint_agent.shared.settings import Settings
from customer_complaint_agent.shared.tool import ToolRuntime
from tests.support.fake_model_clients import create_fake_vision_model_registry


def test_get_email_tool_returns_existing_email() -> None:
    tool = GetEmailTool(Store())

    result = tool.execute({"email_id": "E001"}, _tool_runtime())

    assert result.tool_name == "get_email"
    assert result.arguments == {"email_id": "E001"}
    email = result.data["email"]
    assert isinstance(email, Email)
    assert email.email_id == "E001"


def test_get_email_tool_returns_not_found_for_missing_email() -> None:
    tool = GetEmailTool(Store())

    result = tool.execute({"email_id": "missing"}, _tool_runtime())

    assert result.tool_name == "get_email"
    assert result.arguments == {"email_id": "missing"}
    assert result.data == {"email": None}


def test_get_order_tool_returns_existing_order() -> None:
    tool = GetOrderTool(Store())

    result = tool.execute({"order_id": "O001"}, _tool_runtime())

    assert result.tool_name == "get_order"
    assert result.arguments == {"order_id": "O001"}
    order = result.data["order"]
    assert isinstance(order, Order)
    assert order.order_id == "O001"


def test_get_order_tool_returns_not_found_for_missing_order() -> None:
    tool = GetOrderTool(Store())

    result = tool.execute({"order_id": "missing"}, _tool_runtime())

    assert result.tool_name == "get_order"
    assert result.arguments == {"order_id": "missing"}
    assert result.data == {"order": None}


def test_get_product_tool_returns_existing_product() -> None:
    tool = GetProductTool(Store())

    result = tool.execute({"product_id": "P001"}, _tool_runtime())

    assert result.tool_name == "get_product"
    assert result.arguments == {"product_id": "P001"}
    product = result.data["product"]
    assert isinstance(product, Product)
    assert product.product_id == "P001"


def test_get_product_tool_returns_not_found_for_missing_product() -> None:
    tool = GetProductTool(Store())

    result = tool.execute({"product_id": "missing"}, _tool_runtime())

    assert result.tool_name == "get_product"
    assert result.arguments == {"product_id": "missing"}
    assert result.data == {"product": None}


def test_get_customer_tool_returns_existing_customer() -> None:
    tool = GetCustomerTool(Store())

    result = tool.execute({"customer_id": "C001"}, _tool_runtime())

    assert result.tool_name == "get_customer"
    assert result.arguments == {"customer_id": "C001"}
    customer = result.data["customer"]
    assert isinstance(customer, Customer)
    assert customer.customer_id == "C001"


def test_get_customer_tool_returns_not_found_for_missing_customer() -> None:
    tool = GetCustomerTool(Store())

    result = tool.execute({"customer_id": "missing"}, _tool_runtime())

    assert result.tool_name == "get_customer"
    assert result.arguments == {"customer_id": "missing"}
    assert result.data == {"customer": None}


def test_verify_damaged_product_tool_verifies_broken_attachment() -> None:
    tool = VerifyDamagedProductTool()

    result = tool.execute(
        {"filename": "broken-mug.jpg"},
        _tool_runtime(),
    )

    assert result.tool_name == "verify_damaged_product"
    assert result.arguments == {"filename": "broken-mug.jpg"}
    assert result.data == {
        "filename": "broken-mug.jpg",
        "attachment_exists": True,
        "damage_verified": True,
        "confidence": 1.0,
        "supporting_text": "The filename indicates a broken product.",
    }


def test_verify_damaged_product_tool_rejects_unbroken_attachment() -> None:
    tool = VerifyDamagedProductTool()

    result = tool.execute(
        {"filename": "unbroken-necklace.jpg"},
        _tool_runtime(),
    )

    assert result.tool_name == "verify_damaged_product"
    assert result.arguments == {"filename": "unbroken-necklace.jpg"}
    assert result.data == {
        "filename": "unbroken-necklace.jpg",
        "attachment_exists": True,
        "damage_verified": False,
        "confidence": 1.0,
        "supporting_text": "The filename does not indicate a broken product.",
    }


def test_verify_damaged_product_tool_reports_missing_attachment() -> None:
    tool = VerifyDamagedProductTool()

    result = tool.execute(
        {"filename": "missing.jpg"},
        _tool_runtime(),
    )

    assert result.tool_name == "verify_damaged_product"
    assert result.arguments == {"filename": "missing.jpg"}
    assert result.data == {
        "filename": "missing.jpg",
        "attachment_exists": False,
        "damage_verified": False,
        "confidence": 0.0,
        "supporting_text": "Attachment file was not found.",
    }


def test_evaluate_refund_policy_tool_declines_already_refunded_order() -> None:
    result = EvaluateRefundPolicyTool().execute(
        {
            "already_refunded": True,
            "product_price": 25.0,
            "damage_verified": True,
        },
        _tool_runtime(),
    )

    assert result.tool_name == "evaluate_refund_policy"
    assert result.arguments == {
        "already_refunded": True,
        "product_price": 25.0,
        "damage_verified": True,
    }
    refund_decision = result.data["refund_decision"]
    assert isinstance(refund_decision, RefundDecision)
    assert refund_decision.decision_type == "decline"
    assert refund_decision.reason_code == "already_refunded"


def test_evaluate_refund_policy_tool_declines_unverified_damage() -> None:
    result = EvaluateRefundPolicyTool().execute(
        {
            "already_refunded": False,
            "product_price": 25.0,
            "damage_verified": False,
        },
        _tool_runtime(),
    )

    refund_decision = result.data["refund_decision"]
    assert isinstance(refund_decision, RefundDecision)
    assert refund_decision.decision_type == "decline"
    assert refund_decision.reason_code == "damage_not_verified"


def test_evaluate_refund_policy_tool_refunds_cheap_damaged_product() -> None:
    result = EvaluateRefundPolicyTool().execute(
        {
            "already_refunded": False,
            "product_price": 25.0,
            "damage_verified": True,
        },
        _tool_runtime(),
    )

    refund_decision = result.data["refund_decision"]
    assert isinstance(refund_decision, RefundDecision)
    assert refund_decision.decision_type == "refund"
    assert refund_decision.reason_code == "damaged_cheap_item"


def test_evaluate_refund_policy_tool_escalates_expensive_damaged_product() -> None:
    result = EvaluateRefundPolicyTool().execute(
        {
            "already_refunded": False,
            "product_price": 100.0,
            "damage_verified": True,
        },
        _tool_runtime(),
    )

    refund_decision = result.data["refund_decision"]
    assert isinstance(refund_decision, RefundDecision)
    assert refund_decision.decision_type == "escalate"
    assert refund_decision.reason_code == "damaged_expensive_item"


def _tool_runtime() -> ToolRuntime:
    return ToolRuntime(
        settings=Settings(
            attachments_directory=Path("data/attachments"),
            max_agent_turns=3,
            max_paid_model_calls=0,
        ),
        model_client_registry=create_fake_vision_model_registry(),
    )

from customer_complaint_agent.agents.skills import (
    COMPLAINT_EMAIL_SKILL,
    COMPLIMENT_EMAIL_SKILL,
)


def test_complaint_email_skill_defines_refund_decision_values() -> None:
    refund_decision_field = COMPLAINT_EMAIL_SKILL.final_detail_fields["refund_decision"]

    assert COMPLAINT_EMAIL_SKILL.name == "complaint_email"
    assert refund_decision_field.allowed_values == {
        "refund": "Issue a refund.",
        "decline": "Do not issue a refund.",
        "escalate": "Human handling is required by refund policy.",
    }


def test_complaint_email_skill_defines_claim_and_fact_vocabulary() -> None:
    assert COMPLAINT_EMAIL_SKILL.claim_types == {
        "damaged_product": "The customer claims the purchased product was damaged.",
        "late_delivery": "The customer claims the order arrived late.",
    }
    assert "damage_verification" in COMPLAINT_EMAIL_SKILL.fact_types
    assert "refund_policy_evaluated" in COMPLAINT_EMAIL_SKILL.fact_types


def test_complaint_email_skill_defines_policy_and_blocked_reason_codes() -> None:
    reason_code_field = COMPLAINT_EMAIL_SKILL.final_detail_fields["reason_code"]

    assert reason_code_field.allowed_values is not None
    assert reason_code_field.allowed_values["already_refunded"] == (
        "The order has already been refunded."
    )
    assert reason_code_field.allowed_values["refund_policy_unavailable"] == (
        "The refund policy tool result could not be obtained."
    )


def test_compliment_email_skill_defines_response_template() -> None:
    template_field = COMPLIMENT_EMAIL_SKILL.final_detail_fields["email_template"]

    assert COMPLIMENT_EMAIL_SKILL.name == "compliment_email"
    assert template_field.allowed_values == {
        "reply_to_happy_customer": "Use this template for a positive customer email.",
    }


def test_compliment_email_skill_has_no_claim_or_fact_vocabulary() -> None:
    assert COMPLIMENT_EMAIL_SKILL.claim_types == {}
    assert COMPLIMENT_EMAIL_SKILL.fact_types == {}


def test_compliment_email_skill_defines_blocked_reason_code() -> None:
    reason_code_field = COMPLIMENT_EMAIL_SKILL.final_detail_fields["reason_code"]

    assert reason_code_field.allowed_values == {
        "email_not_found": "The referenced email could not be found.",
        "model_client_not_available": (
            "No text model client was available for the LLM-backed agent."
        ),
    }


def test_email_skills_define_model_client_not_available_reason_code() -> None:
    complaint_reason_codes = COMPLAINT_EMAIL_SKILL.final_detail_fields[
        "reason_code"
    ].allowed_values
    compliment_reason_codes = COMPLIMENT_EMAIL_SKILL.final_detail_fields[
        "reason_code"
    ].allowed_values

    assert complaint_reason_codes is not None
    assert compliment_reason_codes is not None
    assert "model_client_not_available" in complaint_reason_codes
    assert "model_client_not_available" in compliment_reason_codes

"""Concrete agent skills for email handling workflows."""

from .skill import AgentSkill, FinalDetailField

COMPLAINT_EMAIL_SKILL = AgentSkill(
    name="complaint_email",
    goal="Resolve a customer complaint email about an order.",
    instructions=(
        "Inspect the customer email, order, product, and available damage "
        "evidence. Do not decide refund eligibility directly. Gather the "
        "already_refunded, product_price, and damage_verified facts, then call "
        "evaluate_refund_policy. Use the refund policy tool result for the "
        "final refund_decision and reason_code. Return blocked only when "
        "required data cannot be obtained using available tools."
    ),
    claim_types={
        "damaged_product": "The customer claims the purchased product was damaged.",
        "late_delivery": "The customer claims the order arrived late.",
    },
    fact_types={
        "damage_verification": (
            "Whether the available attachment evidence verifies product damage."
        ),
        "refund_policy_evaluated": "The refund policy tool has evaluated the facts.",
    },
    final_detail_fields={
        "refund_decision": FinalDetailField(
            description="The refund policy decision returned by the policy tool.",
            allowed_values={
                "refund": "Issue a refund.",
                "decline": "Do not issue a refund.",
                "escalate": "Human handling is required by refund policy.",
            },
        ),
        "reason_code": FinalDetailField(
            description="The reason for the refund decision or blocked goal.",
            allowed_values={
                "already_refunded": "The order has already been refunded.",
                "damage_not_verified": "Product damage was not verified.",
                "damaged_cheap_item": (
                    "Damage was verified and the product is eligible for an "
                    "automatic refund."
                ),
                "damaged_expensive_item": (
                    "Damage was verified but the product price requires human handling."
                ),
                "email_not_found": "The referenced email could not be found.",
                "missing_order_id": "The email does not identify an order.",
                "order_not_found": "The referenced order could not be found.",
                "product_not_found": "The referenced product could not be found.",
                "missing_attachment": (
                    "The complaint requires damage evidence but no attachment "
                    "was provided."
                ),
                "damage_verification_unavailable": (
                    "Damage verification could not be completed from available tools."
                ),
                "refund_policy_unavailable": (
                    "The refund policy tool result could not be obtained."
                ),
                "model_client_not_available": (
                    "No text model client was available for the LLM-backed agent."
                ),
            },
        ),
    },
)

COMPLIMENT_EMAIL_SKILL = AgentSkill(
    name="compliment_email",
    goal="Prepare a courteous response to a positive customer email.",
    instructions=(
        "Inspect the customer email. Prepare a thank-you response using the "
        "reply_to_happy_customer template. If the email includes a photo "
        "attachment, include a brief customization that acknowledges the photo."
    ),
    claim_types={},
    fact_types={},
    final_detail_fields={
        "email_template": FinalDetailField(
            description="The response template to use for the customer email.",
            allowed_values={
                "reply_to_happy_customer": (
                    "Use this template for a positive customer email."
                ),
            },
        ),
        "email_customization": FinalDetailField(
            description=(
                "Optional short natural-language customization for the response."
            ),
        ),
        "reason_code": FinalDetailField(
            description="The reason the compliment email goal was blocked.",
            allowed_values={
                "email_not_found": "The referenced email could not be found.",
                "model_client_not_available": (
                    "No text model client was available for the LLM-backed agent."
                ),
            },
        ),
    },
)

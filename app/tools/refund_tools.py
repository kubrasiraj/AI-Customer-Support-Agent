
from sqlalchemy.orm import Session

from app.models.order import Order


# Refunds above this amount require human approval.
REFUND_LIMIT_REQUIRING_APPROVAL = 10000


def normalize_refund_reason(reason: str) -> str | None:
    """
    Map common customer phrases to supported refund categories.
    """

    normalized_reason = " ".join(
        reason.lower().strip().replace("-", " ").split()
    )

    damaged_phrases = [
        "damaged",
        "arrived broken",
        "broken item",
        "product broken",
        "product arrived damaged",
        "item arrived damaged",
    ]

    wrong_product_phrases = [
        "wrong product",
        "wrong item",
        "incorrect item",
        "incorrect product",
        "different product delivered",
    ]

    manufacturing_defect_phrases = [
        "manufacturing defect",
        "manufacturing defective",
        "factory defect",
        "product is defective",
        "defective product",
    ]

    if any(
        phrase in normalized_reason
        for phrase in damaged_phrases
    ):
        return "damaged"

    if any(
        phrase in normalized_reason
        for phrase in wrong_product_phrases
    ):
        return "wrong product"

    if any(
        phrase in normalized_reason
        for phrase in manufacturing_defect_phrases
    ):
        return "manufacturing defect"

    return None


def check_refund_eligibility(
    db: Session,
    order_number: str,
    reason: str,
    customer_id: int,
) -> dict:
    """
    Check refund eligibility using the available order data.

    This tool does not create, approve, or process refunds.
    """

    # Step 1: Find the order.
    order = (
        db.query(Order)
        .filter(
            Order.order_number == order_number.strip(),
            Order.customer_id == customer_id,
        )
        .first()
    )

    if order is None:
        return {
            "eligible": False,
            "reason": "Order not found.",
            "requires_human_approval": False,
        }

    # Step 2: Validate the refund reason.
    refund_category = normalize_refund_reason(reason)

    if refund_category is None:
        return {
            "eligible": False,
            "reason": (
                "The refund reason is not recognized. Supported "
                "reasons include damaged products, wrong products, "
                "and manufacturing defects."
            ),
            "requires_human_approval": False,
            "order_number": order.order_number,
        }

    # Step 3: Verify that the order is recorded as delivered.
    if order.status.strip().lower() != "delivered":
        return {
            "eligible": False,
            "reason": (
                "Refund eligibility cannot be confirmed because "
                "the order is not recorded as delivered. "
                f"Current order status: {order.status}."
            ),
            "requires_human_approval": False,
            "order_number": order.order_number,
            "refund_category": refund_category,
        }

    # Step 4: The current Order model has no delivery-date field.
    # Do not use created_at as a substitute for delivery date.
    return {
        "eligible": False,
        "reason": (
            "The order is marked as delivered, but the system does "
            "not store its delivery date. The 30-day refund window "
            "cannot be verified. Delivery-date verification is "
            "required before eligibility can be confirmed."
        ),
        "requires_human_approval": False,
        "order_number": order.order_number,
        "refund_category": refund_category,
    }


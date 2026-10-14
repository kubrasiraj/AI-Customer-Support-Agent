
from sqlalchemy.orm import Session

from app.models.order import Order


def get_order(
    db: Session,
    order_number: str,
    customer_id: int,
) -> dict | None:
    """Return an order only if it belongs to the authenticated customer."""

    order = (
        db.query(Order)
        .filter(
            Order.order_number == order_number.strip(),
            Order.customer_id == customer_id,
        )
        .first()
    )

    if order is None:
        return None

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "status": order.status,
        "total_amount": float(order.total_amount),
    }


def get_order_status(
    db: Session,
    order_number: str,
    customer_id: int,
) -> str | None:
    """Return order status only for the authenticated customer's order."""

    order = (
        db.query(Order)
        .filter(
            Order.order_number == order_number.strip(),
            Order.customer_id == customer_id,
        )
        .first()
    )

    if order is None:
        return None

    return order.status

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user import User


def get_customer(
    db: Session,
    customer_id: int,
) -> dict | None:
    """Return a customer's basic profile."""

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if customer is None:
        return None

    user = (
        db.query(User)
        .filter(User.id == customer.user_id)
        .first()
    )

    return {
        "customer_id": customer.id,
        "name": customer.full_name,
        "email": user.email if user else None,
    }
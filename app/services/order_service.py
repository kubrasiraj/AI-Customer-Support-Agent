from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate


def get_customer_by_user_id(
    db: Session,
    user_id: int,
) -> Customer | None:
    """Find the customer profile linked to a user."""

    return (
        db.query(Customer)
        .filter(Customer.user_id == user_id)
        .first()
    )


def get_customer_order(
    db: Session,
    order_id: int,
    user_id: int,
) -> Order | None:
    """Find an order only if it belongs to the authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        return None

    return (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.customer_id == customer.id,
        )
        .first()
    )


def create_order(
    db: Session,
    user_id: int,
    data: OrderCreate,
) -> Order:
    """Create an order and its order items."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        raise ValueError("Customer profile not found")

    # Start the order total from zero.
    total_amount = Decimal("0.00")

    # Generate a readable order number.
    order_number = (
        f"ORD-{datetime.now().strftime('%Y%m%d')}-"
        f"{user_id}-{int(datetime.now().timestamp())}"
    )

    # Create the main order.
    order = Order(
        order_number=order_number,
        customer_id=customer.id,
        status="pending",
        total_amount=Decimal("0.00"),
    )

    db.add(order)

    # Get the generated order ID.
    db.flush()

    # Create order items.
    for item_data in data.items:

        product = (
            db.query(Product)
            .filter(
                Product.id == item_data.product_id,
                Product.is_active.is_(True),
            )
            .first()
        )

        if not product:
            raise ValueError(
                f"Product {item_data.product_id} not found"
            )

        unit_price = Decimal(str(product.price))

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
        )

        db.add(order_item)

        # Calculate total.
        total_amount += (
            unit_price * item_data.quantity
        )

    # Save calculated total in the order.
    order.total_amount = total_amount

    db.commit()
    db.refresh(order)

    return order
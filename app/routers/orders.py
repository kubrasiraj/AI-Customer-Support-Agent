from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import create_order as create_order_service


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def get_customer_for_user(
    db: Session,
    user_id: int,
) -> Customer | None:
    """Find the customer profile linked to the authenticated user."""

    return (
        db.query(Customer)
        .filter(Customer.user_id == user_id)
        .first()
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an order for the authenticated customer."""

    customer = get_customer_for_user(
        db,
        current_user.id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    try:
        order = create_order_service(
            db,
            current_user.id,
            data,
        )

        return order

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[OrderResponse],
)
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return only the orders belonging to the authenticated customer."""

    customer = get_customer_for_user(
        db,
        current_user.id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return one order only if it belongs to the authenticated customer."""

    customer = get_customer_for_user(
        db,
        current_user.id,
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(
            Order.id == order_id,
            Order.customer_id == customer.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order
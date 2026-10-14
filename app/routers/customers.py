from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerResponse


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get(
    "/me",
    response_model=CustomerResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the profile of the currently authenticated customer."""

    customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found",
        )

    return customer
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.products import ProductCreate, ProductResponse


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a product for testing the support system."""

    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return active products."""

    return (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.id)
        .all()
    )
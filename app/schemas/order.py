from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    """Data required to add a product to an order."""

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    """Data required to create an order."""

    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    """Order item returned by the API."""

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = {
        "from_attributes": True
    }


class OrderResponse(BaseModel):
    """Complete order returned by the API."""

    id: int
    order_number: str
    customer_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {
        "from_attributes": True
    }


class OrderListResponse(BaseModel):
    """Paginated order response."""

    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
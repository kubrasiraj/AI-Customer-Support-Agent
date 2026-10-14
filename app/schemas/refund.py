from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RefundCreate(BaseModel):
    order_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, decimal_places=2)
    reason: str = Field(
        min_length=5,
        max_length=2000,
    )


class RefundResponse(BaseModel):
    id: int
    order_id: int
    customer_id: int
    amount: Decimal
    reason: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RefundApproval(BaseModel):
    approved: bool
    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class RefundListResponse(BaseModel):
    items: list[RefundResponse]
    total: int
    page: int
    page_size: int
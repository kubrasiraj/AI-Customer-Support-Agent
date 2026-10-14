from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
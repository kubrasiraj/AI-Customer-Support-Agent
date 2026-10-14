from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """Data required to create a customer profile."""

    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)


class CustomerUpdate(BaseModel):
    """Data allowed when updating a customer profile."""

    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)


class CustomerResponse(BaseModel):
    """Customer information returned by the API."""

    id: int
    user_id: int
    full_name: str
    phone: str | None
    address: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
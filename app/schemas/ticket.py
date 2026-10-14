from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    subject: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=10,
        max_length=5000,
    )

    priority: str = Field(
        default="normal",
        pattern="^(low|normal|high|urgent)$",
    )


class TicketUpdate(BaseModel):
    """
    Customer can update ticket details,
    but cannot change the ticket status.
    """

    subject: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=5000,
    )

    priority: str | None = Field(
        default=None,
        pattern="^(low|normal|high|urgent)$",
    )


class TicketResponse(BaseModel):
    id: int
    customer_id: int
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
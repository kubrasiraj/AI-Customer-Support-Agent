from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.ticket_service import (
    create_ticket,
    get_customer_tickets,
    get_ticket,
    update_ticket,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new support ticket."""

    try:
        return create_ticket(
            db,
            current_user.id,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=TicketListResponse,
)
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tickets belonging to the authenticated customer."""

    try:
        tickets = get_customer_tickets(
            db,
            current_user.id,
        )

        return TicketListResponse(
            items=tickets,
            total=len(tickets),
            page=1,
            page_size=len(tickets),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_support_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get one ticket owned by the authenticated customer."""

    ticket = get_ticket(
        db,
        ticket_id,
        current_user.id,
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_support_ticket(
    ticket_id: int,
    data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update customer-editable ticket fields."""

    try:
        return update_ticket(
            db,
            ticket_id,
            current_user.id,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
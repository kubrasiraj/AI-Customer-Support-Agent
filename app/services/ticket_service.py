from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate


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


def create_ticket(
    db: Session,
    user_id: int,
    data: TicketCreate,
) -> Ticket:
    """Create a support ticket for the authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        raise ValueError("Customer profile not found")

    ticket = Ticket(
        customer_id=customer.id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status="open",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def get_customer_tickets(
    db: Session,
    user_id: int,
) -> list[Ticket]:
    """Return all tickets belonging to the authenticated customer."""

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        raise ValueError("Customer profile not found")

    return (
        db.query(Ticket)
        .filter(Ticket.customer_id == customer.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


def get_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
) -> Ticket | None:
    """
    Find a ticket only if it belongs
    to the authenticated customer.
    """

    customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if not customer:
        return None

    return (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.customer_id == customer.id,
        )
        .first()
    )


def update_ticket(
    db: Session,
    ticket_id: int,
    user_id: int,
    data: TicketUpdate,
) -> Ticket:
    """Update customer-editable ticket fields."""

    ticket = get_ticket(
        db,
        ticket_id,
        user_id,
    )

    if not ticket:
        raise ValueError("Ticket not found")

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    return ticket
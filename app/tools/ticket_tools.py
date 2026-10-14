
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


def get_ticket(
    db: Session,
    ticket_id: int,
    customer_id: int,
) -> dict | None:
    """Return a ticket only if it belongs to the authenticated customer."""

    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.customer_id == customer_id,
        )
        .first()
    )

    if ticket is None:
        return None

    return {
        "ticket_id": ticket.id,
        "customer_id": ticket.customer_id,
        "status": ticket.status,
        "subject": ticket.subject,
        "description": ticket.description,
    }
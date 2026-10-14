
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.ticket import Ticket
from app.tools.ticket_tools import get_ticket


def test_get_ticket_tool_returns_ticket_details():
    db = MagicMock()

    ticket = SimpleNamespace(
        id=1,
        customer_id=10,
        status="open",
        subject="Delivery issue",
        description="My order has not arrived.",
    )

    db.query.return_value.filter.return_value.first.return_value = ticket

    result = get_ticket(db, ticket_id=1, customer_id=10)

    assert result == {
        "ticket_id": 1,
        "customer_id": 10,
        "status": "open",
        "subject": "Delivery issue",
        "description": "My order has not arrived.",
    }

    db.query.assert_called_once_with(Ticket)


def test_get_ticket_tool_returns_none_when_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = get_ticket(db, ticket_id=999, customer_id=10)

    assert result is None


def test_get_ticket_tool_returns_none_for_another_customer():
    db = MagicMock()

    # Simulate the database finding no ticket matching
    # both the ticket ID and the supplied customer ID.
    db.query.return_value.filter.return_value.first.return_value = None

    result = get_ticket(db, ticket_id=1, customer_id=20)

    assert result is None

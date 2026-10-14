
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.customer import Customer
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services import ticket_service


def test_get_customer_by_user_id():
    db = MagicMock()
    customer = SimpleNamespace(id=10, user_id=101)

    db.query.return_value.filter.return_value.first.return_value = customer

    result = ticket_service.get_customer_by_user_id(db, 101)

    assert result is customer
    db.query.assert_called_once_with(Customer)


def test_create_ticket_success(monkeypatch):
    db = MagicMock()
    customer = SimpleNamespace(id=10)

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    data = TicketCreate(
        subject="Order delivery issue",
        description="My order has not arrived yet.",
        priority="high",
    )

    result = ticket_service.create_ticket(db, 101, data)

    assert isinstance(result, Ticket)
    assert result.customer_id == 10
    assert result.subject == "Order delivery issue"
    assert result.description == "My order has not arrived yet."
    assert result.priority == "high"
    assert result.status == "open"

    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_create_ticket_without_customer(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: None,
    )

    data = TicketCreate(
        subject="Order delivery issue",
        description="My order has not arrived yet.",
    )

    with pytest.raises(ValueError, match="Customer profile not found"):
        ticket_service.create_ticket(db, 101, data)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_get_customer_tickets_without_customer(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: None,
    )

    with pytest.raises(ValueError, match="Customer profile not found"):
        ticket_service.get_customer_tickets(db, 101)

    db.query.assert_not_called()


def test_get_customer_tickets_success(monkeypatch):
    db = MagicMock()
    customer = SimpleNamespace(id=10)
    tickets = [SimpleNamespace(id=2), SimpleNamespace(id=1)]

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    query = db.query.return_value
    query.filter.return_value.order_by.return_value.all.return_value = tickets

    result = ticket_service.get_customer_tickets(db, 101)

    assert result == tickets
    db.query.assert_called_once_with(Ticket)


def test_get_ticket_without_customer(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: None,
    )

    result = ticket_service.get_ticket(db, 1, 101)

    assert result is None
    db.query.assert_not_called()


def test_get_ticket_for_customer(monkeypatch):
    db = MagicMock()
    customer = SimpleNamespace(id=10)
    ticket = SimpleNamespace(id=1, customer_id=10)

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    db.query.return_value.filter.return_value.first.return_value = ticket

    result = ticket_service.get_ticket(db, 1, 101)

    assert result is ticket
    db.query.assert_called_once_with(Ticket)


def test_get_ticket_not_found_for_customer(monkeypatch):
    db = MagicMock()
    customer = SimpleNamespace(id=10)

    monkeypatch.setattr(
        ticket_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    db.query.return_value.filter.return_value.first.return_value = None

    result = ticket_service.get_ticket(db, 999, 101)

    assert result is None


def test_update_ticket_success(monkeypatch):
    db = MagicMock()
    ticket = SimpleNamespace(
        id=1,
        subject="Old subject",
        description="Old description",
        priority="normal",
        status="open",
    )

    monkeypatch.setattr(
        ticket_service,
        "get_ticket",
        lambda db, ticket_id, user_id: ticket,
    )

    data = TicketUpdate(subject="Updated delivery issue")

    result = ticket_service.update_ticket(db, 1, 101, data)

    assert result is ticket
    assert ticket.subject == "Updated delivery issue"
    assert ticket.description == "Old description"
    assert ticket.priority == "normal"
    assert ticket.status == "open"

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(ticket)


def test_update_ticket_only_changes_supplied_fields(monkeypatch):
    db = MagicMock()
    ticket = SimpleNamespace(
        id=1,
        subject="Old subject",
        description="Old description",
        priority="normal",
        status="open",
    )

    monkeypatch.setattr(
        ticket_service,
        "get_ticket",
        lambda db, ticket_id, user_id: ticket,
    )

    data = TicketUpdate(priority="urgent")

    ticket_service.update_ticket(db, 1, 101, data)

    assert ticket.priority == "urgent"
    assert ticket.subject == "Old subject"
    assert ticket.description == "Old description"
    assert ticket.status == "open"


def test_update_ticket_not_found(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(
        ticket_service,
        "get_ticket",
        lambda db, ticket_id, user_id: None,
    )

    with pytest.raises(ValueError, match="Ticket not found"):
        ticket_service.update_ticket(
            db,
            999,
            101,
            TicketUpdate(subject="Updated subject"),
        )

    db.commit.assert_not_called()

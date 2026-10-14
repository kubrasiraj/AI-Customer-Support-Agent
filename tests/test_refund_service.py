
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.refund import RefundCreate
from app.services.refund_service import (
    create_refund_request,
    get_customer_by_user_id,
)
from app.models.refund_request import RefundRequest


def make_query(first_result):
    """Create a mock query whose first() method returns a given result."""
    query = MagicMock()
    query.filter.return_value = query
    query.first.return_value = first_result
    return query


def test_get_customer_by_user_id_returns_customer():
    db = MagicMock()
    customer = SimpleNamespace(id=5, user_id=101)
    db.query.return_value.filter.return_value.first.return_value = customer

    result = get_customer_by_user_id(db, user_id=101)

    assert result is customer
    db.query.assert_called_once()


def test_create_refund_request_success():
    db = MagicMock()

    customer = SimpleNamespace(id=5, user_id=101)
    order = SimpleNamespace(
        id=10,
        customer_id=5,
        total_amount=Decimal("200.00"),
    )

    customer_query = make_query(customer)
    order_query = make_query(order)
    db.query.side_effect = [customer_query, order_query]

    data = RefundCreate(
        order_id=10,
        amount="100.00",
        reason="Product arrived damaged",
    )

    result = create_refund_request(db, user_id=101, data=data)

    assert isinstance(result, RefundRequest)
    assert result.order_id == 10
    assert result.customer_id == 5
    assert result.amount == Decimal("100.00")
    assert result.reason == "Product arrived damaged"
    assert result.status == "pending"

    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_create_refund_request_fails_without_customer():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    data = RefundCreate(
        order_id=10,
        amount="50.00",
        reason="Product arrived damaged",
    )

    with pytest.raises(ValueError, match="Customer profile not found"):
        create_refund_request(db, user_id=999, data=data)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_refund_request_fails_when_order_not_found():
    db = MagicMock()

    customer = SimpleNamespace(id=5, user_id=101)
    db.query.side_effect = [
        make_query(customer),
        make_query(None),
    ]

    data = RefundCreate(
        order_id=999,
        amount="50.00",
        reason="Product arrived damaged",
    )

    with pytest.raises(ValueError, match="Order not found"):
        create_refund_request(db, user_id=101, data=data)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_refund_request_rejects_amount_above_order_total():
    db = MagicMock()

    customer = SimpleNamespace(id=5, user_id=101)
    order = SimpleNamespace(
        id=10,
        customer_id=5,
        total_amount=Decimal("100.00"),
    )

    db.query.side_effect = [
        make_query(customer),
        make_query(order),
    ]

    data = RefundCreate(
        order_id=10,
        amount="150.00",
        reason="Product arrived damaged",
    )

    with pytest.raises(
        ValueError,
        match="Refund amount cannot exceed order total",
    ):
        create_refund_request(db, user_id=101, data=data)

    db.add.assert_not_called()
    db.commit.assert_not_called()

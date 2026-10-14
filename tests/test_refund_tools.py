
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.tools.refund_tools import (
    REFUND_LIMIT_REQUIRING_APPROVAL,
    check_refund_eligibility,
    normalize_refund_reason,
)


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("Damaged product", "damaged"),
        ("  ARRIVED BROKEN  ", "damaged"),
        ("broken-item", "damaged"),
        ("The product arrived damaged", "damaged"),
        ("wrong item", "wrong product"),
        ("Incorrect product delivered", "wrong product"),
        ("different product delivered", "wrong product"),
        ("manufacturing defect", "manufacturing defect"),
        ("Factory defect", "manufacturing defect"),
        ("defective product", "manufacturing defect"),
        ("I changed my mind", None),
        ("", None),
    ],
)
def test_normalize_refund_reason(reason, expected):
    assert normalize_refund_reason(reason) == expected


def make_order(
    order_number="ORD-100",
    customer_id=7,
    status="delivered",
):
    return SimpleNamespace(
        order_number=order_number,
        customer_id=customer_id,
        status=status,
    )


def make_db(order):
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = order
    return db


def test_refund_order_not_found():
    db = make_db(None)

    result = check_refund_eligibility(
        db=db,
        order_number="ORD-100",
        reason="damaged product",
        customer_id=7,
    )

    assert result == {
        "eligible": False,
        "reason": "Order not found.",
        "requires_human_approval": False,
    }


def test_unknown_refund_reason_is_rejected():
    db = make_db(make_order())

    result = check_refund_eligibility(
        db=db,
        order_number="ORD-100",
        reason="I changed my mind",
        customer_id=7,
    )

    assert result["eligible"] is False
    assert result["requires_human_approval"] is False
    assert result["order_number"] == "ORD-100"
    assert "not recognized" in result["reason"]


@pytest.mark.parametrize(
    "status",
    ["pending", "processing", "shipped", "cancelled"],
)
def test_refund_rejected_when_order_not_delivered(status):
    db = make_db(make_order(status=status))

    result = check_refund_eligibility(
        db=db,
        order_number="ORD-100",
        reason="damaged product",
        customer_id=7,
    )

    assert result["eligible"] is False
    assert result["requires_human_approval"] is False
    assert result["order_number"] == "ORD-100"
    assert result["refund_category"] == "damaged"
    assert status in result["reason"]


def test_refund_rejected_when_delivery_date_cannot_be_verified():
    db = make_db(make_order(status="delivered"))

    result = check_refund_eligibility(
        db=db,
        order_number="ORD-100",
        reason="wrong item",
        customer_id=7,
    )

    assert result["eligible"] is False
    assert result["requires_human_approval"] is False
    assert result["order_number"] == "ORD-100"
    assert result["refund_category"] == "wrong product"
    assert "delivery date" in result["reason"].lower()
    assert "30-day refund window" in result["reason"]


def test_order_number_is_stripped_before_lookup():
    db = make_db(make_order(order_number="ORD-100"))

    check_refund_eligibility(
        db=db,
        order_number="  ORD-100  ",
        reason="damaged product",
        customer_id=7,
    )

    db.query.return_value.filter.assert_called_once()


def test_refund_approval_limit_is_defined():
    assert REFUND_LIMIT_REQUIRING_APPROVAL == 10000


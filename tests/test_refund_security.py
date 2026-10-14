
from unittest.mock import MagicMock

from app.services.refund_service import get_customer_refund


def test_refund_lookup_returns_none_if_customer_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = get_customer_refund(
        db,
        refund_id=1,
        user_id=999,
    )

    assert result is None

    # Without a customer profile, the refund table is never queried.
    assert db.query.call_count == 1


def test_refund_lookup_returns_none_if_refund_not_owned():
    db = MagicMock()

    customer = type(
        "CustomerStub",
        (),
        {"id": 5, "user_id": 101},
    )()

    customer_query = MagicMock()
    customer_query.filter.return_value = customer_query
    customer_query.first.return_value = customer

    refund_query = MagicMock()
    refund_query.filter.return_value = refund_query
    refund_query.first.return_value = None

    db.query.side_effect = [customer_query, refund_query]

    result = get_customer_refund(
        db,
        refund_id=999,
        user_id=101,
    )

    assert result is None
    assert db.query.call_count == 2

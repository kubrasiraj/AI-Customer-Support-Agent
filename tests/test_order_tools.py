
from decimal import Decimal
from types import SimpleNamespace

from app.models.order import Order
from app.tools.order_tools import get_order, get_order_status



class FakeQuery:
    def __init__(self, order):
        self.order = order
        self.filters = []

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self

    def first(self):
        return self.order





class FakeDB:
    def __init__(self, order=None):
        self.order = order
        self.last_query = None

    def query(self, model):
        assert model is Order
        self.last_query = FakeQuery(self.order)
        return self.last_query


def make_order():
    return SimpleNamespace(
        id=55,
        order_number="ORD-123",
        customer_id=20,
        status="processing",
        total_amount=Decimal("8500.00"),
    )


def test_get_order_returns_order_details():
    db = FakeDB(order=make_order())

    result = get_order(
        db=db,
        order_number="ORD-123",
        customer_id=20,
    )

    assert result == {
        "order_id": 55,
        "order_number": "ORD-123",
        "customer_id": 20,
        "status": "processing",
        "total_amount": 8500.0,
    }


def test_get_order_strips_whitespace_from_order_number():
    db = FakeDB(order=make_order())

    result = get_order(
        db=db,
        order_number="  ORD-123  ",
        customer_id=20,
    )

    assert result is not None
    assert result["order_number"] == "ORD-123"


def test_get_order_returns_none_when_order_missing():
    db = FakeDB(order=None)

    result = get_order(
        db=db,
        order_number="ORD-MISSING",
        customer_id=20,
    )

    assert result is None


def test_get_order_status_returns_status():
    db = FakeDB(order=make_order())

    result = get_order_status(
        db=db,
        order_number="ORD-123",
        customer_id=20,
    )

    assert result == "processing"


def test_get_order_status_returns_none_when_order_missing():
    db = FakeDB(order=None)

    result = get_order_status(
        db=db,
        order_number="ORD-MISSING",
        customer_id=20,
    )

    assert result is None


def test_get_order_converts_decimal_total_to_float():
    db = FakeDB(order=make_order())

    result = get_order(
        db=db,
        order_number="ORD-123",
        customer_id=20,
    )

    assert result["total_amount"] == 8500.0
    assert isinstance(result["total_amount"], float)


def test_get_order_filters_by_authenticated_customer():
    db = FakeDB(order=make_order())

    get_order(
        db=db,
        order_number="ORD-123",
        customer_id=99,
    )

    filter_text = " ".join(
        str(condition) for condition in db.last_query.filters
    )

    assert "orders.order_number" in filter_text
    assert "orders.customer_id" in filter_text

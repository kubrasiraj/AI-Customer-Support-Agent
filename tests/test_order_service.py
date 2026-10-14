
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate
from app.services import order_service


class FakeQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if self.model is Customer:
            return self.db.customer

        if self.model is Order:
            return self.db.order

        if self.model is Product:
            if self.db.product_results:
                return self.db.product_results.pop(0)
            return None

        return None


class FakeDB:
    def __init__(
        self,
        customer=None,
        order=None,
        product_results=None,
    ):
        self.customer = customer
        self.order = order
        self.product_results = list(product_results or [])
        self.added = []
        self.committed = False
        self.refreshed = []
        self.flush_count = 0

    def query(self, model):
        return FakeQuery(self, model)

    def add(self, obj):
        self.added.append(obj)

        if isinstance(obj, Order) and obj.id is None:
            obj.id = 123

    def flush(self):
        self.flush_count += 1

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)


def make_customer():
    return SimpleNamespace(id=20, user_id=10)


def make_order():
    return Order(
        id=55,
        order_number="ORD-123",
        customer_id=20,
        status="pending",
        total_amount=Decimal("100.00"),
    )


def make_order_data(items):
    return OrderCreate(items=items)


def test_get_customer_by_user_id_returns_customer():
    customer = make_customer()
    db = FakeDB(customer=customer)

    result = order_service.get_customer_by_user_id(db, 10)

    assert result is customer


def test_get_customer_by_user_id_returns_none_when_missing():
    db = FakeDB(customer=None)

    result = order_service.get_customer_by_user_id(db, 999)

    assert result is None


def test_get_customer_order_returns_owned_order(monkeypatch):
    customer = make_customer()
    order = make_order()
    db = FakeDB(customer=customer, order=order)

    monkeypatch.setattr(
        order_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    result = order_service.get_customer_order(
        db=db,
        order_id=55,
        user_id=10,
    )

    assert result is order


def test_get_customer_order_returns_none_without_customer(monkeypatch):
    db = FakeDB()

    monkeypatch.setattr(
        order_service,
        "get_customer_by_user_id",
        lambda db, user_id: None,
    )

    result = order_service.get_customer_order(
        db=db,
        order_id=55,
        user_id=999,
    )

    assert result is None


def test_get_customer_order_returns_none_when_order_missing(monkeypatch):
    customer = make_customer()
    db = FakeDB(customer=customer, order=None)

    monkeypatch.setattr(
        order_service,
        "get_customer_by_user_id",
        lambda db, user_id: customer,
    )

    result = order_service.get_customer_order(
        db=db,
        order_id=999,
        user_id=10,
    )

    assert result is None


def test_create_order_calculates_total_and_saves_items(monkeypatch):
    customer = make_customer()

    product_one = SimpleNamespace(
        id=1,
        price=Decimal("8500.00"),
        is_active=True,
    )
    product_two = SimpleNamespace(
        id=2,
        price=Decimal("1500.00"),
        is_active=True,
    )

    db = FakeDB(
        customer=customer,
        product_results=[product_one, product_two],
    )

    data = make_order_data(
        [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 3},
        ]
    )

    # Avoid dependence on the actual system clock.
    class FixedDateTime:
        @staticmethod
        def now():
            return datetime_for_test

    from datetime import datetime
    datetime_for_test = datetime(2026, 10, 13, 12, 0, 0)

    monkeypatch.setattr(
        order_service,
        "datetime",
        FixedDateTime,
    )

    result = order_service.create_order(
        db=db,
        user_id=10,
        data=data,
    )

    assert result.customer_id == 20
    assert result.status == "pending"
    assert result.total_amount == Decimal("21500.00")
    assert result.order_number.startswith("ORD-20261013-10-")
    assert db.flush_count == 1
    assert db.committed is True
    assert db.refreshed == [result]

    order_items = [
        obj for obj in db.added
        if isinstance(obj, OrderItem)
    ]

    assert len(order_items) == 2
    assert order_items[0].product_id == 1
    assert order_items[0].quantity == 2
    assert order_items[0].unit_price == Decimal("8500.00")
    assert order_items[1].product_id == 2
    assert order_items[1].quantity == 3
    assert order_items[1].unit_price == Decimal("1500.00")


def test_create_order_raises_when_customer_missing():
    db = FakeDB(customer=None)
    data = make_order_data(
        [{"product_id": 1, "quantity": 1}]
    )

    with pytest.raises(
        ValueError,
        match="Customer profile not found",
    ):
        order_service.create_order(
            db=db,
            user_id=999,
            data=data,
        )

    assert db.committed is False


def test_create_order_raises_when_product_missing():
    db = FakeDB(
        customer=make_customer(),
        product_results=[None],
    )
    data = make_order_data(
        [{"product_id": 999, "quantity": 1}]
    )

    with pytest.raises(
        ValueError,
        match="Product 999 not found",
    ):
        order_service.create_order(
            db=db,
            user_id=10,
            data=data,
        )

    assert db.committed is False


def test_create_order_uses_decimal_price_without_float_rounding():
    product = SimpleNamespace(
        id=1,
        price=Decimal("19.99"),
        is_active=True,
    )
    db = FakeDB(
        customer=make_customer(),
        product_results=[product],
    )
    data = make_order_data(
        [{"product_id": 1, "quantity": 3}]
    )

    result = order_service.create_order(
        db=db,
        user_id=10,
        data=data,
    )

    assert result.total_amount == Decimal("59.97")
    assert isinstance(result.total_amount, Decimal)


def test_create_order_uses_generated_order_id_for_items():
    product = SimpleNamespace(
        id=7,
        price=Decimal("25.00"),
        is_active=True,
    )
    db = FakeDB(
        customer=make_customer(),
        product_results=[product],
    )
    data = make_order_data(
        [{"product_id": 7, "quantity": 2}]
    )

    result = order_service.create_order(
        db=db,
        user_id=10,
        data=data,
    )

    order_items = [
        obj for obj in db.added
        if isinstance(obj, OrderItem)
    ]

    assert result.id == 123
    assert len(order_items) == 1
    assert order_items[0].order_id == 123
    assert result.total_amount == Decimal("50.00")

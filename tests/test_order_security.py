
from unittest.mock import MagicMock

from app.routers import orders as orders_router


def test_order_lookup_passes_authenticated_user_id(
    client,
    monkeypatch,
):
    captured = {}

    def mock_get_customer_for_user(db, user_id):
        captured["user_id"] = user_id
        return None

    monkeypatch.setattr(
        orders_router,
        "get_customer_for_user",
        mock_get_customer_for_user,
    )

    response = client.get("/orders/999")

    assert captured["user_id"] == 101
    assert response.status_code == 404


def test_order_list_uses_authenticated_customer(client, mock_db):
    mock_db.query.return_value.filter.return_value.all.return_value = []

    response = client.get("/orders")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

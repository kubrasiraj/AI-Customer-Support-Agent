
from datetime import datetime
from types import SimpleNamespace


def test_customer_can_access_own_profile(client, mock_db):
    customer = SimpleNamespace(
        id=5,
        user_id=101,
        full_name="Test Customer",
        phone="03001234567",
        address="Karachi",
        created_at=datetime(2026, 10, 13, 10, 0, 0),
    )

    mock_db.query.return_value.filter.return_value.first.return_value = customer

    response = client.get("/customers/me")

    assert response.status_code == 200
    assert response.json()["user_id"] == 101
    assert response.json()["full_name"] == "Test Customer"


def test_customer_profile_missing_returns_404(client, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/customers/me")

    assert response.status_code == 404

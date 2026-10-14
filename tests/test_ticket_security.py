
from app.routers import tickets as tickets_router


def test_ticket_lookup_uses_authenticated_user(
    client,
    monkeypatch,
):
    captured = {}

    def mock_get_ticket(db, ticket_id, user_id):
        captured["ticket_id"] = ticket_id
        captured["user_id"] = user_id
        return None

    monkeypatch.setattr(
        tickets_router,
        "get_ticket",
        mock_get_ticket,
    )

    response = client.get("/tickets/999")

    assert captured["ticket_id"] == 999
    assert captured["user_id"] == 101
    assert response.status_code == 404

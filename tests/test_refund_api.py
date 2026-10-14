
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.routers import refunds as refund_router


def make_refund(
    refund_id=1,
    order_id=10,
    customer_id=5,
    amount=Decimal("100.00"),
    reason="Product arrived damaged",
    status="pending",
):
    """Build a mock refund compatible with RefundResponse."""
    return SimpleNamespace(
        id=refund_id,
        order_id=order_id,
        customer_id=customer_id,
        amount=amount,
        reason=reason,
        status=status,
        created_at=datetime(2026, 10, 13, 10, 0, 0),
    )


def test_create_refund_returns_201(client, monkeypatch):
    refund = make_refund()

    def mock_create(db, user_id, data):
        assert user_id == 101
        assert data.order_id == 10
        return refund

    monkeypatch.setattr(
        refund_router,
        "create_refund_request",
        mock_create,
    )

    response = client.post(
        "/refunds",
        json={
            "order_id": 10,
            "amount": "100.00",
            "reason": "Product arrived damaged",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["status"] == "pending"


def test_create_refund_rejects_invalid_body(client, monkeypatch):
    def unexpected_call(*args, **kwargs):
        pytest.fail("Refund service should not be called")

    monkeypatch.setattr(
        refund_router,
        "create_refund_request",
        unexpected_call,
    )

    response = client.post(
        "/refunds",
        json={
            "order_id": 0,
            "amount": "100.00",
            "reason": "Product arrived damaged",
        },
    )

    assert response.status_code == 422


def test_create_refund_maps_service_error_to_400(
    client,
    monkeypatch,
):
    def mock_create(db, user_id, data):
        raise ValueError("Order not found")

    monkeypatch.setattr(
        refund_router,
        "create_refund_request",
        mock_create,
    )

    response = client.post(
        "/refunds",
        json={
            "order_id": 10,
            "amount": "50.00",
            "reason": "Product arrived damaged",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Order not found"


def test_get_my_refunds_returns_list(client, monkeypatch):
    refunds = [
        make_refund(refund_id=1),
        make_refund(
            refund_id=2,
            amount=Decimal("50.00"),
        ),
    ]

    def mock_get_refunds(db, user_id):
        assert user_id == 101
        return refunds

    monkeypatch.setattr(
        refund_router,
        "get_customer_refunds",
        mock_get_refunds,
    )

    response = client.get("/refunds")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2


def test_get_my_refunds_maps_missing_customer_to_404(
    client,
    monkeypatch,
):
    def mock_get_refunds(db, user_id):
        raise ValueError("Customer profile not found")

    monkeypatch.setattr(
        refund_router,
        "get_customer_refunds",
        mock_get_refunds,
    )

    response = client.get("/refunds")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer profile not found"


def test_get_missing_refund_returns_404(client, monkeypatch):
    monkeypatch.setattr(
        refund_router,
        "get_refund",
        lambda db, refund_id, user_id: None,
    )

    response = client.get("/refunds/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Refund not found"


def test_customer_cannot_review_refund(client, monkeypatch):
    def unexpected_call(*args, **kwargs):
        pytest.fail("Unauthorized customer reached refund review service")

    monkeypatch.setattr(
        refund_router,
        "approve_or_reject_refund",
        unexpected_call,
    )

    response = client.post(
        "/refunds/1/approval",
        json={
            "approved": True,
            "note": "Reviewed",
        },
    )

    assert response.status_code == 403


def test_admin_can_review_refund(client, admin_user, monkeypatch):
    from app.core.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: admin_user

    try:
        approved_refund = make_refund(status="approved")

        def mock_review(
            db,
            refund_id,
            reviewer_id,
            reviewer_role,
            approved,
            note,
        ):
            assert refund_id == 1
            assert reviewer_id == 202
            assert reviewer_role == "admin"
            assert approved is True
            assert note == "Reviewed"
            return approved_refund

        monkeypatch.setattr(
            refund_router,
            "approve_or_reject_refund",
            mock_review,
        )

        response = client.post(
            "/refunds/1/approval",
            json={
                "approved": True,
                "note": "Reviewed",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"
    finally:
        app.dependency_overrides.pop(get_current_user, None)

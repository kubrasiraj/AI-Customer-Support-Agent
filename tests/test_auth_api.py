
from types import SimpleNamespace

from app.routers import auth as auth_router


def make_user():
    return SimpleNamespace(
        id=101,
        email="customer@example.com",
        role="customer",
        is_active=True,
    )


def test_register_endpoint_success(client, monkeypatch):
    user = make_user()

    monkeypatch.setattr(
        auth_router,
        "register_user",
        lambda db, data: user,
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test Customer",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 101
    assert response.json()["email"] == "customer@example.com"
    assert response.json()["role"] == "customer"


def test_register_endpoint_rejects_duplicate_email(
    client,
    monkeypatch,
):
    def duplicate_registration(db, data):
        raise ValueError("Email is already registered")

    monkeypatch.setattr(
        auth_router,
        "register_user",
        duplicate_registration,
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "SecurePassword123!",
            "full_name": "Existing User",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_register_endpoint_rejects_invalid_body(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "short",
            "full_name": "A",
        },
    )

    assert response.status_code == 422


def test_login_endpoint_success(client, monkeypatch):
    user = make_user()

    monkeypatch.setattr(
        auth_router,
        "authenticate_user",
        lambda db, data: user,
    )
    monkeypatch.setattr(
        auth_router,
        "create_user_token",
        lambda authenticated_user: "test-access-token",
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "customer@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "test-access-token",
        "token_type": "bearer",
    }


def test_login_endpoint_rejects_invalid_credentials(
    client,
    monkeypatch,
):
    def reject_login(db, data):
        raise ValueError("Invalid email or password")

    monkeypatch.setattr(
        auth_router,
        "authenticate_user",
        reject_login,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "customer@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_endpoint_rejects_invalid_body(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "",
        },
    )

    assert response.status_code == 422

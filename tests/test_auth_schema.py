
import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


def test_register_request_accepts_valid_data():
    data = RegisterRequest(
        email="customer@example.com",
        password="SecurePassword123!",
        full_name="Test Customer",
    )

    assert data.email == "customer@example.com"
    assert data.phone is None
    assert data.address is None


def test_register_request_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="customer@example.com",
            password="short",
            full_name="Test Customer",
        )


def test_register_request_rejects_password_over_72_characters():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="customer@example.com",
            password="A" * 73,
            full_name="Test Customer",
        )


def test_register_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="SecurePassword123!",
            full_name="Test Customer",
        )


def test_register_request_rejects_short_name():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="customer@example.com",
            password="SecurePassword123!",
            full_name="A",
        )


def test_login_request_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(
            email="customer@example.com",
            password="",
        )


def test_token_response_defaults_to_bearer():
    response = TokenResponse(
        access_token="example-token",
    )

    assert response.token_type == "bearer"


def test_user_response_accepts_valid_data():
    response = UserResponse(
        id=101,
        email="customer@example.com",
        role="customer",
        is_active=True,
    )

    assert response.id == 101
    assert response.is_active is True

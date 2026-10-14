
import pytest
from unittest.mock import MagicMock

from app.models.customer import Customer
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth_service


def make_register_data():
    return RegisterRequest(
        email="new@example.com",
        password="SecurePassword123!",
        full_name="Test Customer",
        phone="03001234567",
        address="Karachi",
    )


def make_login_data():
    return LoginRequest(
        email="customer@example.com",
        password="SecurePassword123!",
    )


def make_db(existing_user=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = (
        existing_user
    )
    return db


def test_get_user_by_email_returns_user():
    user = User(
        email="customer@example.com",
        hashed_password="hashed",
    )
    db = make_db(user)

    result = auth_service.get_user_by_email(
        db,
        "customer@example.com",
    )

    assert result is user


def test_get_user_by_email_returns_none_when_missing():
    db = make_db(None)

    result = auth_service.get_user_by_email(
        db,
        "missing@example.com",
    )

    assert result is None


def test_register_user_successfully(monkeypatch):
    db = make_db(None)

    monkeypatch.setattr(
        auth_service,
        "hash_password",
        lambda password: "hashed-password",
    )

    # Simulate the database assigning an ID during flush.
    def assign_user_id():
        added_user = db.add.call_args.args[0]
        added_user.id = 123

    db.flush.side_effect = assign_user_id

    result = auth_service.register_user(
        db,
        make_register_data(),
    )

    assert isinstance(result, User)
    assert result.id == 123
    assert result.email == "new@example.com"
    assert result.hashed_password == "hashed-password"

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    assert len(added_objects) == 2
    assert isinstance(added_objects[0], User)
    assert isinstance(added_objects[1], Customer)
    assert added_objects[1].user_id == 123

    db.flush.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_register_user_rejects_duplicate_email():
    existing_user = User(
        email="existing@example.com",
        hashed_password="hashed",
    )
    db = make_db(existing_user)

    data = RegisterRequest(
        email="existing@example.com",
        password="SecurePassword123!",
        full_name="Existing User",
    )

    with pytest.raises(
        ValueError,
        match="Email is already registered",
    ):
        auth_service.register_user(db, data)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_authenticate_user_rejects_unknown_email():
    db = make_db(None)

    with pytest.raises(
        ValueError,
        match="Invalid email or password",
    ):
        auth_service.authenticate_user(
            db,
            make_login_data(),
        )


def test_authenticate_user_rejects_wrong_password(monkeypatch):
    user = User(
        email="customer@example.com",
        hashed_password="stored-hash",
    )
    user.id = 101
    user.is_active = True

    db = make_db(user)

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: False,
    )

    with pytest.raises(
        ValueError,
        match="Invalid email or password",
    ):
        auth_service.authenticate_user(
            db,
            make_login_data(),
        )


def test_authenticate_user_rejects_inactive_account(monkeypatch):
    user = User(
        email="customer@example.com",
        hashed_password="stored-hash",
    )
    user.id = 101
    user.is_active = False

    db = make_db(user)

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: True,
    )

    with pytest.raises(
        ValueError,
        match="User account is inactive",
    ):
        auth_service.authenticate_user(
            db,
            make_login_data(),
        )


def test_authenticate_user_successfully(monkeypatch):
    user = User(
        email="customer@example.com",
        hashed_password="stored-hash",
    )
    user.id = 101
    user.is_active = True

    db = make_db(user)

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, hashed: True,
    )

    result = auth_service.authenticate_user(
        db,
        make_login_data(),
    )

    assert result is user


def test_create_user_token(monkeypatch):
    user = User(
        email="customer@example.com",
        hashed_password="hashed",
    )
    user.id = 101

    token_payload = {}

    def fake_create_access_token(data):
        token_payload.update(data)
        return "test-access-token"

    monkeypatch.setattr(
        auth_service,
        "create_access_token",
        fake_create_access_token,
    )

    result = auth_service.create_user_token(user)

    assert result == "test-access-token"
    assert token_payload == {
        "sub": "101",
        "email": "customer@example.com",
    }

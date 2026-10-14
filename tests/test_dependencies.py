
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user, require_role
from app.core.security import create_access_token


def make_credentials(token: str):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def make_user(
    user_id=101,
    role="customer",
    is_active=True,
):
    return SimpleNamespace(
        id=user_id,
        email="customer@example.com",
        role=role,
        is_active=is_active,
    )


def make_db(user):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


def test_valid_token_returns_current_user():
    user = make_user()
    db = make_db(user)
    token = create_access_token({"sub": str(user.id)})

    result = get_current_user(
        credentials=make_credentials(token),
        db=db,
    )

    assert result.id == user.id
    assert result.email == user.email


def test_invalid_token_returns_401():
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=make_credentials("invalid.token.value"),
            db=db,
        )

    assert exc.value.status_code == 401
    db.query.assert_not_called()


def test_token_without_subject_returns_401():
    token = create_access_token({"email": "customer@example.com"})
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=make_credentials(token),
            db=db,
        )

    assert exc.value.status_code == 401
    db.query.assert_not_called()


def test_non_numeric_subject_returns_401():
    token = create_access_token({"sub": "not-a-user-id"})
    db = MagicMock()

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=make_credentials(token),
            db=db,
        )

    assert exc.value.status_code == 401
    db.query.assert_not_called()


def test_nonexistent_user_returns_401():
    token = create_access_token({"sub": "999"})
    db = make_db(None)

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=make_credentials(token),
            db=db,
        )

    assert exc.value.status_code == 401


def test_inactive_user_returns_403():
    user = make_user(is_active=False)
    token = create_access_token({"sub": str(user.id)})
    db = make_db(user)

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=make_credentials(token),
            db=db,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Inactive user account"


def test_admin_role_rejects_customer():
    customer = make_user(role="customer")
    admin_checker = require_role("admin")

    with pytest.raises(HTTPException) as exc:
        admin_checker(current_user=customer)

    assert exc.value.status_code == 403


def test_admin_role_allows_admin():
    admin = make_user(role="admin")
    admin_checker = require_role("admin")

    result = admin_checker(current_user=admin)

    assert result.id == admin.id
    assert result.role == "admin"

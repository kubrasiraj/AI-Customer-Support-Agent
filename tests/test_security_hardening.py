
import pytest
from fastapi import HTTPException

from app.core.dependencies import require_role


def test_customer_is_denied_admin_permission(customer_user):
    checker = require_role("admin")

    with pytest.raises(HTTPException) as exc:
        checker(current_user=customer_user)

    assert exc.value.status_code == 403


def test_admin_is_allowed_admin_permission(admin_user):
    checker = require_role("admin")

    result = checker(current_user=admin_user)

    assert result is admin_user


def test_admin_is_denied_support_only_permission(admin_user):
    checker = require_role("support")

    with pytest.raises(HTTPException) as exc:
        checker(current_user=admin_user)

    assert exc.value.status_code == 403


def test_customer_is_allowed_customer_permission(customer_user):
    checker = require_role("customer")

    result = checker(current_user=customer_user)

    assert result is customer_user

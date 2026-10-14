
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.db.database import get_db


@pytest.fixture
def mock_db():
    """Provide a mock database session for isolated tests."""
    return MagicMock()


@pytest.fixture
def customer_user():
    """Represent an authenticated customer."""
    return SimpleNamespace(
        id=101,
        email="customer@example.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def admin_user():
    """Represent an authenticated administrator."""
    return SimpleNamespace(
        id=202,
        email="admin@example.com",
        role="admin",
        is_active=True,
    )


@pytest.fixture
def client(mock_db, customer_user):
    """Create a test client without connecting to the real database."""

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = (
        lambda: customer_user
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

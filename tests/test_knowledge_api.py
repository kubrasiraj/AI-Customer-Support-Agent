
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.main import app
from app.routers import knowledge as knowledge_router



@pytest.fixture
def knowledge_client(mock_db, admin_user):
    """Create a test client authenticated as an admin."""

    from fastapi.testclient import TestClient

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_upload_rejects_unsupported_file_type(knowledge_client):
    response = knowledge_client.post(
        "/knowledge/documents",
        files={"file": ("malware.exe", b"example", "application/octet-stream")},
        data={"title": "Test", "category": "general"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only .txt and .pdf files are supported"
    )


def test_upload_rejects_customer(client):
    response = client.post(
        "/knowledge/documents",
        files={"file": ("policy.txt", b"Refund policy", "text/plain")},
        data={"title": "Refund policy", "category": "refund"},
    )

    assert response.status_code == 403


def test_reindex_returns_404_when_document_missing(
    knowledge_client,
    mock_db,
):
    query = mock_db.query.return_value
    query.filter.return_value.first.return_value = None

    response = knowledge_client.post(
        "/knowledge/documents/999/reindex"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge document not found"


def test_background_processing_uses_separate_session(monkeypatch):
    fake_db = MagicMock()
    fake_document = SimpleNamespace(id=7)

    fake_db.query.return_value.filter.return_value.first.return_value = (
        fake_document
    )

    session_factory = MagicMock(return_value=fake_db)
    processor = MagicMock(return_value=3)

    monkeypatch.setattr(
        knowledge_router,
        "SessionLocal",
        session_factory,
    )
    monkeypatch.setattr(
        knowledge_router,
        "process_knowledge_document",
        processor,
    )

    knowledge_router.process_document_in_background(7)

    session_factory.assert_called_once_with()
    processor.assert_called_once_with(fake_db, fake_document)
    fake_db.close.assert_called_once()

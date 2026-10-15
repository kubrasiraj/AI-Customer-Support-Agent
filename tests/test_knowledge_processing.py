
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.services.knowledge_service as module


@pytest.fixture
def document():
    return SimpleNamespace(
        id=10,
        file_path="refund_policy.txt",
        status="uploaded",
    )


def test_process_document_success(monkeypatch, document):
    db = MagicMock()

    monkeypatch.setattr(
        module,
        "extract_text",
        lambda _path: "Refunds are allowed under company policy.",
    )

    monkeypatch.setattr(
        module,
        "embed_knowledge_chunks",
        lambda _db, document_id: 1,
    )

    result = module.process_knowledge_document(db, document)

    assert result == 1
    assert document.status == "processed"
    assert db.add.call_count == 1
    assert db.commit.call_count == 3


def test_process_document_fails_when_text_is_empty(
    monkeypatch,
    document,
):
    db = MagicMock()

    monkeypatch.setattr(
        module,
        "extract_text",
        lambda _path: "   ",
    )

    with pytest.raises(
        ValueError,
        match="No text could be extracted",
    ):
        module.process_knowledge_document(db, document)

    assert document.status == "failed"
    db.rollback.assert_called_once()


def test_process_document_fails_when_embedding_fails(
    monkeypatch,
    document,
):
    db = MagicMock()

    monkeypatch.setattr(
        module,
        "extract_text",
        lambda _path: "Refunds are allowed under company policy.",
    )

    def fail_embedding(_db, _document_id):
        raise RuntimeError("Embedding failed")

    monkeypatch.setattr(
        module,
        "embed_knowledge_chunks",
        fail_embedding,
    )

    with pytest.raises(RuntimeError, match="Embedding failed"):
        module.process_knowledge_document(db, document)

    assert document.status == "failed"
    db.rollback.assert_called_once()
